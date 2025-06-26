import numpy as np
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from core.model import StructuralModel
from solver.matrix_assembler import MatrixAssembler
from solver.linear_solver import LinearSolver
from solver.modal_analyzer import ModalAnalyzer
from db.models import AnalysisResult, LoadCombination
import json
import logging
from datetime import datetime


class AnalysisEngine:
    """Main analysis engine that coordinates all analysis types"""
    
    def __init__(self, structural_model: StructuralModel):
        self.model = structural_model
        self.db = structural_model.db
        
        # Analysis components
        self.matrix_assembler = None
        self.linear_solver = None
        self.modal_analyzer = None
        
        # Results storage
        self.analysis_results = {}
        
    def prepare_analysis(self) -> bool:
        """Prepare model for analysis"""
        
        # Validate model
        is_valid, errors = self.model.validate_model()
        if not is_valid:
            logging.error(f"Model validation failed: {errors}")
            return False
        
        # Get model components
        nodes = self.model.node_manager.get_all_nodes()
        elements = self.model.element_manager.get_all_elements()
        materials = {m.id: m for m in self.model.material_manager.get_all_materials()}
        sections = {s.id: s for s in self.model.section_manager.get_all_sections()}
        
        # Get boundary conditions
        boundary_conditions = []
        for node in nodes:
            bc = self.model.node_manager.get_boundary_condition(node.id)
            if bc:
                boundary_conditions.append(bc)
        
        # Create matrix assembler
        self.matrix_assembler = MatrixAssembler(
            nodes, elements, materials, sections, boundary_conditions
        )
        
        logging.info("Analysis preparation completed successfully")
        return True
    
    def run_linear_static_analysis(self, load_combination_name: str = None) -> Dict[str, Any]:
        """Run linear static analysis"""
        
        if not self.matrix_assembler:
            if not self.prepare_analysis():
                return {"status": "failed", "error": "Model preparation failed"}
        
        try:
            # Assemble global stiffness matrix
            logging.info("Assembling global stiffness matrix...")
            K_global = self.matrix_assembler.assemble_global_stiffness_matrix()
            
            # Get loads and load combination
            loads = self.model.load_manager.get_all_loads()
            
            load_factors = None
            if load_combination_name:
                load_combinations = self.model.load_manager.get_all_load_combinations()
                for combo in load_combinations:
                    if combo.name == load_combination_name:
                        load_factors = combo.factors
                        break
                
                if load_factors is None:
                    logging.warning(f"Load combination '{load_combination_name}' not found. Using unit factors.")
            
            # Assemble load vector
            logging.info("Assembling load vector...")
            F_global = self.matrix_assembler.assemble_load_vector(loads, load_factors)
            
            # Create and run linear solver
            logging.info("Solving linear system...")
            self.linear_solver = LinearSolver(K_global, F_global)
            results = self.linear_solver.solve()
            
            if results['status'] == 'converged':
                # Calculate additional results
                node_indices = list(range(len(self.matrix_assembler.nodes)))
                
                # Get nodal displacements
                nodal_displacements = self.linear_solver.get_nodal_displacements(node_indices)
                
                # Get reaction forces at supports
                restrained_indices = []
                for i, node_id in enumerate(self.matrix_assembler.node_ids):
                    if node_id in self.matrix_assembler.boundary_conditions:
                        restrained_indices.append(i)
                
                reaction_forces = self.linear_solver.get_reaction_forces(restrained_indices)
                
                # Calculate element forces
                elements = self.model.element_manager.get_all_elements()
                nodes = self.matrix_assembler.nodes
                materials = self.matrix_assembler.materials
                sections = self.matrix_assembler.sections
                node_to_index = self.matrix_assembler.node_to_index
                
                element_forces = self.linear_solver.calculate_element_forces(
                    elements, nodes, materials, sections, node_to_index
                )
                
                # Store results in database
                analysis_result = AnalysisResult(
                    model_id=self.model.model.id,
                    analysis_type="linear_static",
                    load_combination=load_combination_name or "unit",
                    status="completed",
                    node_displacements=nodal_displacements,
                    element_forces=element_forces,
                    reaction_forces=reaction_forces,
                    completed_at=datetime.utcnow()
                )
                
                self.db.add(analysis_result)
                self.db.commit()
                
                # Compile complete results
                complete_results = {
                    "status": "completed",
                    "analysis_type": "linear_static",
                    "load_combination": load_combination_name or "unit",
                    "nodal_displacements": nodal_displacements,
                    "element_forces": element_forces,
                    "reaction_forces": reaction_forces,
                    "max_displacements": self.linear_solver.get_maximum_displacements(),
                    "equilibrium_check": self.linear_solver.check_equilibrium(F_global),
                    "analysis_id": analysis_result.id
                }
                
                self.analysis_results["linear_static"] = complete_results
                logging.info("Linear static analysis completed successfully")
                
                return complete_results
            
            else:
                logging.error("Linear static analysis failed to converge")
                return results
                
        except Exception as e:
            logging.error(f"Linear static analysis failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def run_modal_analysis(self, num_modes: int = 10) -> Dict[str, Any]:
        """Run modal analysis"""
        
        if not self.matrix_assembler:
            if not self.prepare_analysis():
                return {"status": "failed", "error": "Model preparation failed"}
        
        try:
            # Assemble global matrices
            logging.info("Assembling global stiffness matrix...")
            K_global = self.matrix_assembler.assemble_global_stiffness_matrix()
            
            logging.info("Assembling global mass matrix...")
            M_global = self.matrix_assembler.assemble_global_mass_matrix()
            
            # Create and run modal analyzer
            logging.info(f"Solving eigenvalue problem for {num_modes} modes...")
            self.modal_analyzer = ModalAnalyzer(K_global, M_global)
            results = self.modal_analyzer.solve(num_modes)
            
            if results['status'] == 'converged':
                # Get additional modal data
                node_indices = list(range(len(self.matrix_assembler.nodes)))
                mode_shapes = self.modal_analyzer.export_mode_shapes(node_indices)
                mode_summary = self.modal_analyzer.get_mode_summary()
                
                # Store results in database
                analysis_result = AnalysisResult(
                    model_id=self.model.model.id,
                    analysis_type="modal",
                    status="completed",
                    mode_shapes=mode_shapes,
                    completed_at=datetime.utcnow()
                )
                
                self.db.add(analysis_result)
                self.db.commit()
                
                # Compile complete results
                complete_results = {
                    "status": "completed",
                    "analysis_type": "modal",
                    "num_modes": num_modes,
                    "frequencies": results['frequencies'].tolist(),
                    "periods": results['periods'].tolist(),
                    "mode_shapes": mode_shapes,
                    "mode_summary": mode_summary,
                    "analysis_id": analysis_result.id
                }
                
                self.analysis_results["modal"] = complete_results
                logging.info("Modal analysis completed successfully")
                
                return complete_results
            
            else:
                logging.error("Modal analysis failed to converge")
                return results
                
        except Exception as e:
            logging.error(f"Modal analysis failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def run_response_spectrum_analysis(self, spectrum_data: Dict[str, Any], 
                                     damping_ratio: float = 0.05,
                                     combination_method: str = 'CQC') -> Dict[str, Any]:
        """Run response spectrum analysis"""
        
        # First run modal analysis if not already done
        if not self.modal_analyzer:
            modal_results = self.run_modal_analysis()
            if modal_results['status'] != 'completed':
                return modal_results
        
        try:
            logging.info("Running response spectrum analysis...")
            
            # Extract spectrum data
            spectrum_periods = np.array(spectrum_data['periods'])
            spectrum_values = np.array(spectrum_data['accelerations'])
            
            # Run response spectrum analysis
            rs_results = self.modal_analyzer.calculate_response_spectrum_analysis(
                spectrum_values, spectrum_periods, damping_ratio, combination_method
            )
            
            # Convert modal displacements to nodal format
            node_indices = list(range(len(self.matrix_assembler.nodes)))
            nodal_displacements = {}
            
            combined_displacements = rs_results['combined_displacements']
            
            for i, node_index in enumerate(node_indices):
                start_dof = i * 6
                nodal_displacements[node_index] = {
                    'ux': combined_displacements[start_dof + 0],
                    'uy': combined_displacements[start_dof + 1],
                    'uz': combined_displacements[start_dof + 2],
                    'rx': combined_displacements[start_dof + 3],
                    'ry': combined_displacements[start_dof + 4],
                    'rz': combined_displacements[start_dof + 5]
                }
            
            # Store results in database
            analysis_result = AnalysisResult(
                model_id=self.model.model.id,
                analysis_type="response_spectrum",
                status="completed",
                node_displacements=nodal_displacements,
                completed_at=datetime.utcnow()
            )
            
            self.db.add(analysis_result)
            self.db.commit()
            
            # Compile complete results
            complete_results = {
                "status": "completed",
                "analysis_type": "response_spectrum",
                "nodal_displacements": nodal_displacements,
                "spectrum_data": spectrum_data,
                "damping_ratio": damping_ratio,
                "combination_method": combination_method,
                "modal_participation": self.modal_analyzer.get_modal_participation_factors(),
                "analysis_id": analysis_result.id
            }
            
            self.analysis_results["response_spectrum"] = complete_results
            logging.info("Response spectrum analysis completed successfully")
            
            return complete_results
            
        except Exception as e:
            logging.error(f"Response spectrum analysis failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def run_all_load_combinations(self) -> Dict[str, Any]:
        """Run linear static analysis for all load combinations"""
        
        load_combinations = self.model.load_manager.get_all_load_combinations()
        
        if not load_combinations:
            logging.warning("No load combinations found")
            return {"status": "failed", "error": "No load combinations defined"}
        
        all_results = {}
        
        for combination in load_combinations:
            logging.info(f"Running analysis for load combination: {combination.name}")
            
            result = self.run_linear_static_analysis(combination.name)
            all_results[combination.name] = result
        
        return {
            "status": "completed",
            "analysis_type": "multiple_load_combinations",
            "combinations": all_results,
            "num_combinations": len(load_combinations)
        }
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all completed analyses"""
        
        # Get completed analyses from database
        completed_analyses = self.db.query(AnalysisResult).filter(
            AnalysisResult.model_id == self.model.model.id,
            AnalysisResult.status == "completed"
        ).all()
        
        summary = {
            "model_id": self.model.model.id,
            "total_analyses": len(completed_analyses),
            "analysis_types": [],
            "latest_results": {}
        }
        
        for analysis in completed_analyses:
            if analysis.analysis_type not in summary["analysis_types"]:
                summary["analysis_types"].append(analysis.analysis_type)
            
            # Keep latest result for each analysis type
            if (analysis.analysis_type not in summary["latest_results"] or 
                analysis.completed_at > summary["latest_results"][analysis.analysis_type]["completed_at"]):
                
                summary["latest_results"][analysis.analysis_type] = {
                    "id": analysis.id,
                    "completed_at": analysis.completed_at,
                    "load_combination": analysis.load_combination
                }
        
        return summary
    
    def export_analysis_results(self, analysis_type: str = None) -> Dict[str, Any]:
        """Export analysis results for external use"""
        
        if analysis_type and analysis_type in self.analysis_results:
            return self.analysis_results[analysis_type]
        
        return self.analysis_results
    
    def clear_results(self):
        """Clear all analysis results"""
        
        # Clear from database
        self.db.query(AnalysisResult).filter(
            AnalysisResult.model_id == self.model.model.id
        ).delete()
        self.db.commit()
        
        # Clear from memory
        self.analysis_results.clear()
        
        logging.info("All analysis results cleared")
