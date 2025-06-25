import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import eigsh
import logging


class ModalAnalyzer:
    """Modal analysis solver for eigenvalue problems"""
    
    def __init__(self, stiffness_matrix: csc_matrix, mass_matrix: csc_matrix):
        self.K = stiffness_matrix
        self.M = mass_matrix
        self.eigenvalues = None
        self.eigenvectors = None
        self.frequencies = None
        self.periods = None
        self.solved = False
        
        # Analysis parameters
        self.num_modes = 10
        self.shift = 0.0
        self.tolerance = 1e-8
        
        # Results storage
        self.results = {}
    
    def solve(self, num_modes: int = 10, shift: float = 0.0) -> Dict:
        """Solve eigenvalue problem (K - λM)φ = 0"""
        
        self.num_modes = min(num_modes, self.K.shape[0] - 1)
        self.shift = shift
        
        try:
            # Solve generalized eigenvalue problem
            eigenvalues, eigenvectors = eigsh(
                self.K, 
                k=self.num_modes, 
                M=self.M, 
                sigma=self.shift,
                which='LM',
                tol=self.tolerance
            )
            
            # Sort by frequency (eigenvalue)
            sort_indices = np.argsort(eigenvalues)
            self.eigenvalues = eigenvalues[sort_indices]
            self.eigenvectors = eigenvectors[:, sort_indices]
            
            # Calculate frequencies and periods
            self.frequencies = np.sqrt(np.abs(self.eigenvalues)) / (2 * np.pi)
            self.periods = 1.0 / self.frequencies
            
            # Normalize mode shapes
            self._normalize_mode_shapes()
            
            self.solved = True
            
            # Store results
            self.results = {
                'eigenvalues': self.eigenvalues,
                'eigenvectors': self.eigenvectors,
                'frequencies': self.frequencies,
                'periods': self.periods,
                'status': 'converged',
                'num_modes': self.num_modes
            }
            
            logging.info(f"Modal analysis completed: {self.num_modes} modes found")
            
        except Exception as e:
            self.results = {
                'eigenvalues': np.array([]),
                'eigenvectors': np.array([]),
                'frequencies': np.array([]),
                'periods': np.array([]),
                'status': 'failed',
                'error': str(e),
                'num_modes': 0
            }
            
            logging.error(f"Modal analysis failed: {str(e)}")
        
        return self.results
    
    def _normalize_mode_shapes(self):
        """Normalize mode shapes with respect to mass matrix"""
        
        for i in range(self.num_modes):
            mode = self.eigenvectors[:, i]
            
            # Mass normalize: φᵀMφ = 1
            modal_mass = mode.T @ self.M @ mode
            if modal_mass > 0:
                self.eigenvectors[:, i] = mode / np.sqrt(modal_mass)
            
            # Ensure consistent sign convention (largest component positive)
            max_idx = np.argmax(np.abs(self.eigenvectors[:, i]))
            if self.eigenvectors[max_idx, i] < 0:
                self.eigenvectors[:, i] *= -1
    
    def get_mode_shape(self, mode_number: int, node_indices: List[int], 
                      dof_per_node: int = 6) -> Dict[int, Dict]:
        """Get mode shape displacements for specific nodes"""
        
        if not self.solved:
            raise ValueError("Modal analysis not solved yet")
        
        if mode_number >= self.num_modes:
            raise ValueError(f"Mode {mode_number} not available. Only {self.num_modes} modes computed.")
        
        mode_shape = {}
        mode_vector = self.eigenvectors[:, mode_number]
        
        for node_index in node_indices:
            start_dof = node_index * dof_per_node
            end_dof = start_dof + dof_per_node
            
            mode_shape[node_index] = {
                'ux': mode_vector[start_dof + 0],
                'uy': mode_vector[start_dof + 1],
                'uz': mode_vector[start_dof + 2],
                'rx': mode_vector[start_dof + 3],
                'ry': mode_vector[start_dof + 4],
                'rz': mode_vector[start_dof + 5]
            }
        
        return mode_shape
    
    def get_modal_participation_factors(self, influence_vector: np.ndarray = None) -> Dict:
        """Calculate modal participation factors"""
        
        if not self.solved:
            raise ValueError("Modal analysis not solved yet")
        
        if influence_vector is None:
            # Default: unit acceleration in Z direction (seismic analysis)
            influence_vector = np.zeros(self.M.shape[0])
            influence_vector[2::6] = 1.0  # Z direction for all nodes
        
        participation_factors = np.zeros(self.num_modes)
        effective_masses = np.zeros(self.num_modes)
        
        for i in range(self.num_modes):
            mode = self.eigenvectors[:, i]
            
            # Participation factor: Γᵢ = φᵢᵀMr / φᵢᵀMφᵢ
            numerator = mode.T @ self.M @ influence_vector
            denominator = mode.T @ self.M @ mode
            
            if abs(denominator) > 1e-12:
                participation_factors[i] = numerator / denominator
                effective_masses[i] = participation_factors[i]**2 * denominator
        
        # Calculate cumulative mass participation
        total_mass = influence_vector.T @ self.M @ influence_vector
        mass_participation_ratio = effective_masses / total_mass if total_mass > 0 else np.zeros_like(effective_masses)
        cumulative_mass_ratio = np.cumsum(mass_participation_ratio)
        
        return {
            'participation_factors': participation_factors,
            'effective_masses': effective_masses,
            'mass_participation_ratio': mass_participation_ratio,
            'cumulative_mass_ratio': cumulative_mass_ratio,
            'total_mass': total_mass
        }
    
    def calculate_response_spectrum_analysis(self, spectrum_values: np.ndarray, 
                                           spectrum_periods: np.ndarray,
                                           damping_ratio: float = 0.05,
                                           combination_method: str = 'CQC') -> Dict:
        """Perform response spectrum analysis"""
        
        if not self.solved:
            raise ValueError("Modal analysis not solved yet")
        
        # Interpolate spectrum values for computed periods
        spectral_accelerations = np.interp(self.periods, spectrum_periods, spectrum_values)
        
        # Calculate modal responses
        modal_responses = {}
        
        # Default influence vector for seismic analysis (Z direction)
        influence_vector = np.zeros(self.M.shape[0])
        influence_vector[2::6] = 1.0
        
        participation_data = self.get_modal_participation_factors(influence_vector)
        participation_factors = participation_data['participation_factors']
        
        # Calculate modal displacement responses
        modal_displacements = np.zeros((self.M.shape[0], self.num_modes))
        
        for i in range(self.num_modes):
            # Modal displacement: uᵢ = Γᵢ φᵢ Sₐᵢ / ωᵢ²
            omega_i = 2 * np.pi * self.frequencies[i]
            if omega_i > 0:
                modal_displacements[:, i] = (participation_factors[i] * 
                                           self.eigenvectors[:, i] * 
                                           spectral_accelerations[i] / omega_i**2)
        
        # Combine modal responses
        if combination_method == 'SRSS':
            # Square Root of Sum of Squares
            combined_displacements = np.sqrt(np.sum(modal_displacements**2, axis=1))
        
        elif combination_method == 'CQC':
            # Complete Quadratic Combination
            combined_displacements = self._cqc_combination(modal_displacements, damping_ratio)
        
        else:
            raise ValueError(f"Unknown combination method: {combination_method}")
        
        modal_responses = {
            'modal_displacements': modal_displacements,
            'combined_displacements': combined_displacements,
            'spectral_accelerations': spectral_accelerations,
            'participation_factors': participation_factors,
            'combination_method': combination_method,
            'damping_ratio': damping_ratio
        }
        
        return modal_responses
    
    def _cqc_combination(self, modal_responses: np.ndarray, damping_ratio: float) -> np.ndarray:
        """Complete Quadratic Combination of modal responses"""
        
        num_dof, num_modes = modal_responses.shape
        combined_response = np.zeros(num_dof)
        
        for i in range(num_dof):
            response_i = modal_responses[i, :]
            
            # Double summation for CQC
            total = 0.0
            for j in range(num_modes):
                for k in range(num_modes):
                    if j == k:
                        correlation_coeff = 1.0
                    else:
                        # Correlation coefficient for CQC
                        freq_ratio = self.frequencies[k] / self.frequencies[j]
                        correlation_coeff = (8 * damping_ratio**2 * (1 + freq_ratio) * freq_ratio**(3/2)) / \
                                          ((1 - freq_ratio**2)**2 + 4 * damping_ratio**2 * freq_ratio * (1 + freq_ratio)**2)
                    
                    total += response_i[j] * response_i[k] * correlation_coeff
            
            combined_response[i] = np.sqrt(abs(total))
        
        return combined_response
    
    def get_mode_summary(self) -> Dict:
        """Get summary of modal analysis results"""
        
        if not self.solved:
            raise ValueError("Modal analysis not solved yet")
        
        # Find dominant direction for each mode
        mode_directions = []
        
        for i in range(self.num_modes):
            mode = self.eigenvectors[:, i]
            
            # Extract translational components
            ux = mode[0::6]
            uy = mode[1::6]
            uz = mode[2::6]
            
            # Calculate RMS values for each direction
            rms_x = np.sqrt(np.mean(ux**2))
            rms_y = np.sqrt(np.mean(uy**2))
            rms_z = np.sqrt(np.mean(uz**2))
            
            # Determine dominant direction
            max_rms = max(rms_x, rms_y, rms_z)
            if max_rms == rms_x:
                direction = 'X-translation'
            elif max_rms == rms_y:
                direction = 'Y-translation'
            else:
                direction = 'Z-translation'
            
            mode_directions.append(direction)
        
        return {
            'num_modes': self.num_modes,
            'frequencies': self.frequencies.tolist(),
            'periods': self.periods.tolist(),
            'mode_directions': mode_directions,
            'fundamental_period': self.periods[0] if len(self.periods) > 0 else 0.0,
            'fundamental_frequency': self.frequencies[0] if len(self.frequencies) > 0 else 0.0
        }
    
    def export_mode_shapes(self, node_indices: List[int], dof_per_node: int = 6) -> Dict:
        """Export mode shapes for visualization"""
        
        if not self.solved:
            raise ValueError("Modal analysis not solved yet")
        
        mode_shapes_data = {}
        
        for mode_num in range(self.num_modes):
            mode_shape = self.get_mode_shape(mode_num, node_indices, dof_per_node)
            
            mode_shapes_data[f'mode_{mode_num + 1}'] = {
                'frequency': self.frequencies[mode_num],
                'period': self.periods[mode_num],
                'mode_shape': mode_shape
            }
        
        return mode_shapes_data
    
    def export_results(self) -> Dict:
        """Export all modal analysis results"""
        
        if not self.solved:
            raise ValueError("Modal analysis not solved yet")
        
        return {
            'analysis_type': 'modal',
            'status': self.results['status'],
            'num_modes': self.num_modes,
            'eigenvalues': self.eigenvalues.tolist(),
            'frequencies': self.frequencies.tolist(),
            'periods': self.periods.tolist(),
            'mode_summary': self.get_mode_summary(),
            'solver_info': {
                'matrix_size': self.K.shape[0],
                'shift': self.shift,
                'tolerance': self.tolerance
            }
        }
