from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.auth import get_current_user
from api.models import get_model_by_id
import re

router = APIRouter(prefix="/api/nlp", tags=["nlp"])

class NLPPrompt(BaseModel):
    prompt: str
    project_id: int
    model_id: int

class NLPResponse(BaseModel):
    actions: List[Dict[str, Any]]
    message: str
    success: bool

# Simple NLP patterns for structural engineering commands
PATTERNS = [
    {
        "pattern": r"(?:create|add|design|make)\s+(?:a\s+)?(\d+)(?:\s*|\-)story\s+building",
        "action": "create_multi_story_building",
        "params": ["num_stories"]
    },
    {
        "pattern": r"(?:create|add|design|make)\s+(?:a\s+)?beam\s+from\s+(?:node\s+)?(\w+)\s+to\s+(?:node\s+)?(\w+)",
        "action": "create_beam",
        "params": ["start_node", "end_node"]
    },
    {
        "pattern": r"(?:create|add|design|make)\s+(?:a\s+)?column\s+from\s+(?:node\s+)?(\w+)\s+to\s+(?:node\s+)?(\w+)",
        "action": "create_column",
        "params": ["start_node", "end_node"]
    },
    {
        "pattern": r"(?:create|add)\s+(?:a\s+)?node\s+at\s+\(?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)?",
        "action": "create_node",
        "params": ["x", "y", "z"]
    },
    {
        "pattern": r"(?:create|add|design|make)\s+(?:a\s+)?grid\s+of\s+(\d+)\s*x\s*(\d+)\s+nodes",
        "action": "create_grid",
        "params": ["rows", "columns"]
    },
    {
        "pattern": r"(?:create|add|design|make)\s+(?:a\s+)?frame\s+with\s+(\d+)\s+bays\s+and\s+(\d+)\s+stories",
        "action": "create_frame",
        "params": ["bays", "stories"]
    },
    {
        "pattern": r"(?:create|add|design|make)\s+(?:a\s+)?truss\s+with\s+(\d+)\s+segments",
        "action": "create_truss",
        "params": ["segments"]
    },
    {
        "pattern": r"(?:set|apply|use)\s+(?:the\s+)?material\s+(?:as\s+)?(\w+)",
        "action": "set_material",
        "params": ["material_type"]
    },
    {
        "pattern": r"(?:clear|reset|delete)\s+(?:the\s+)?model",
        "action": "clear_model",
        "params": []
    }
]

def parse_prompt(prompt: str) -> Dict[str, Any]:
    """Parse a natural language prompt into structured actions"""
    prompt = prompt.lower().strip()
    
    for pattern_info in PATTERNS:
        match = re.search(pattern_info["pattern"], prompt)
        if match:
            action = pattern_info["action"]
            params = {}
            
            # Extract parameters from the match
            for i, param_name in enumerate(pattern_info["params"]):
                params[param_name] = match.group(i+1)
            
            return {
                "action": action,
                "params": params
            }
    
    # If no pattern matches
    return {
        "action": "unknown",
        "params": {},
        "original_prompt": prompt
    }

def create_multi_story_building(model_data: Dict[str, Any], num_stories: int) -> List[Dict[str, Any]]:
    """Create a multi-story building structure"""
    actions = []
    story_height = 3.0  # 3 meters per story
    grid_size = 5.0  # 5x5 meter grid
    
    # Create a 3x3 grid building with the specified number of stories
    nodes = []
    elements = []
    
    # Create nodes for each level
    node_id = 1
    for story in range(num_stories + 1):  # +1 for ground level
        for row in range(3):
            for col in range(3):
                node = {
                    "action": "create_node",
                    "params": {
                        "id": node_id,
                        "label": f"N{node_id}",
                        "position": [col * grid_size, row * grid_size, story * story_height]
                    }
                }
                nodes.append(node)
                node_id += 1
    
    actions.extend(nodes)
    
    # Create columns between levels
    element_id = 1
    for story in range(num_stories):
        for row in range(3):
            for col in range(3):
                # Calculate node IDs
                bottom_node_id = story * 9 + row * 3 + col + 1
                top_node_id = (story + 1) * 9 + row * 3 + col + 1
                
                element = {
                    "action": "create_element",
                    "params": {
                        "id": element_id,
                        "label": f"C{element_id}",
                        "type": "column",
                        "start_node": bottom_node_id,
                        "end_node": top_node_id,
                        "material_type": "concrete"
                    }
                }
                elements.append(element)
                element_id += 1
    
    # Create beams on each level (except ground)
    for story in range(1, num_stories + 1):
        for row in range(3):
            for col in range(2):
                # Horizontal beams in X direction
                start_node_id = story * 9 + row * 3 + col + 1
                end_node_id = story * 9 + row * 3 + col + 2
                
                element = {
                    "action": "create_element",
                    "params": {
                        "id": element_id,
                        "label": f"BX{element_id}",
                        "type": "beam",
                        "start_node": start_node_id,
                        "end_node": end_node_id,
                        "material_type": "concrete"
                    }
                }
                elements.append(element)
                element_id += 1
        
        # Horizontal beams in Y direction
        for row in range(2):
            for col in range(3):
                start_node_id = story * 9 + row * 3 + col + 1
                end_node_id = story * 9 + (row + 1) * 3 + col + 1
                
                element = {
                    "action": "create_element",
                    "params": {
                        "id": element_id,
                        "label": f"BY{element_id}",
                        "type": "beam",
                        "start_node": start_node_id,
                        "end_node": end_node_id,
                        "material_type": "concrete"
                    }
                }
                elements.append(element)
                element_id += 1
    
    actions.extend(elements)
    return actions

def create_frame(model_data: Dict[str, Any], bays: int, stories: int) -> List[Dict[str, Any]]:
    """Create a 2D frame with specified bays and stories"""
    actions = []
    bay_width = 5.0  # 5 meters per bay
    story_height = 3.0  # 3 meters per story
    
    # Create nodes
    nodes = []
    node_id = 1
    
    for story in range(stories + 1):  # +1 for ground level
        for bay in range(bays + 1):  # +1 for end column
            node = {
                "action": "create_node",
                "params": {
                    "id": node_id,
                    "label": f"N{node_id}",
                    "position": [bay * bay_width, 0, story * story_height]
                }
            }
            nodes.append(node)
            node_id += 1
    
    actions.extend(nodes)
    
    # Create columns
    elements = []
    element_id = 1
    
    for story in range(stories):
        for bay in range(bays + 1):
            # Calculate node IDs
            bottom_node_id = story * (bays + 1) + bay + 1
            top_node_id = (story + 1) * (bays + 1) + bay + 1
            
            element = {
                "action": "create_element",
                "params": {
                    "id": element_id,
                    "label": f"C{element_id}",
                    "type": "column",
                    "start_node": bottom_node_id,
                    "end_node": top_node_id,
                    "material_type": "concrete"
                }
            }
            elements.append(element)
            element_id += 1
    
    # Create beams
    for story in range(1, stories + 1):  # Start from first floor (not ground)
        for bay in range(bays):
            # Calculate node IDs
            left_node_id = story * (bays + 1) + bay + 1
            right_node_id = story * (bays + 1) + bay + 2
            
            element = {
                "action": "create_element",
                "params": {
                    "id": element_id,
                    "label": f"B{element_id}",
                    "type": "beam",
                    "start_node": left_node_id,
                    "end_node": right_node_id,
                    "material_type": "concrete"
                }
            }
            elements.append(element)
            element_id += 1
    
    actions.extend(elements)
    return actions

def create_grid(model_data: Dict[str, Any], rows: int, columns: int) -> List[Dict[str, Any]]:
    """Create a grid of nodes"""
    actions = []
    grid_spacing = 5.0  # 5 meters spacing
    
    # Create nodes
    node_id = 1
    for row in range(int(rows)):
        for col in range(int(columns)):
            node = {
                "action": "create_node",
                "params": {
                    "id": node_id,
                    "label": f"N{node_id}",
                    "position": [col * grid_spacing, row * grid_spacing, 0]
                }
            }
            actions.append(node)
            node_id += 1
    
    return actions

def create_node(model_data: Dict[str, Any], x: float, y: float, z: float) -> List[Dict[str, Any]]:
    """Create a single node at the specified coordinates"""
    # Find the next available node ID
    next_id = 1
    if model_data.get("nodes"):
        next_id = max([node.get("id", 0) for node in model_data["nodes"]]) + 1
    
    return [{
        "action": "create_node",
        "params": {
            "id": next_id,
            "label": f"N{next_id}",
            "position": [float(x), float(y), float(z)]
        }
    }]

def create_beam(model_data: Dict[str, Any], start_node: str, end_node: str) -> List[Dict[str, Any]]:
    """Create a beam between two nodes"""
    # Find the nodes by label
    start_node_id = None
    end_node_id = None
    
    for node in model_data.get("nodes", []):
        if node.get("label") == start_node:
            start_node_id = node.get("id")
        elif node.get("label") == end_node:
            end_node_id = node.get("id")
    
    if not start_node_id or not end_node_id:
        return [{
            "action": "error",
            "params": {
                "message": f"Could not find nodes {start_node} and/or {end_node}"
            }
        }]
    
    # Find the next available element ID
    next_id = 1
    if model_data.get("elements"):
        next_id = max([elem.get("id", 0) for elem in model_data["elements"]]) + 1
    
    return [{
        "action": "create_element",
        "params": {
            "id": next_id,
            "label": f"B{next_id}",
            "type": "beam",
            "start_node": start_node_id,
            "end_node": end_node_id,
            "material_type": "concrete"
        }
    }]

def create_column(model_data: Dict[str, Any], start_node: str, end_node: str) -> List[Dict[str, Any]]:
    """Create a column between two nodes"""
    # Find the nodes by label
    start_node_id = None
    end_node_id = None
    
    for node in model_data.get("nodes", []):
        if node.get("label") == start_node:
            start_node_id = node.get("id")
        elif node.get("label") == end_node:
            end_node_id = node.get("id")
    
    if not start_node_id or not end_node_id:
        return [{
            "action": "error",
            "params": {
                "message": f"Could not find nodes {start_node} and/or {end_node}"
            }
        }]
    
    # Find the next available element ID
    next_id = 1
    if model_data.get("elements"):
        next_id = max([elem.get("id", 0) for elem in model_data["elements"]]) + 1
    
    return [{
        "action": "create_element",
        "params": {
            "id": next_id,
            "label": f"C{next_id}",
            "type": "column",
            "start_node": start_node_id,
            "end_node": end_node_id,
            "material_type": "concrete"
        }
    }]

def create_truss(model_data: Dict[str, Any], segments: int) -> List[Dict[str, Any]]:
    """Create a simple truss with the specified number of segments"""
    actions = []
    segment_length = 2.0  # 2 meters per segment
    height = 2.0  # Height of the truss
    
    # Create bottom chord nodes
    nodes = []
    node_id = 1
    
    for i in range(int(segments) + 1):
        node = {
            "action": "create_node",
            "params": {
                "id": node_id,
                "label": f"N{node_id}",
                "position": [i * segment_length, 0, 0]
            }
        }
        nodes.append(node)
        node_id += 1
    
    # Create top chord nodes
    for i in range(int(segments) + 1):
        node = {
            "action": "create_node",
            "params": {
                "id": node_id,
                "label": f"N{node_id}",
                "position": [i * segment_length, 0, height]
            }
        }
        nodes.append(node)
        node_id += 1
    
    actions.extend(nodes)
    
    # Create elements
    elements = []
    element_id = 1
    
    # Bottom chord
    for i in range(int(segments)):
        element = {
            "action": "create_element",
            "params": {
                "id": element_id,
                "label": f"B{element_id}",
                "type": "beam",
                "start_node": i + 1,
                "end_node": i + 2,
                "material_type": "steel"
            }
        }
        elements.append(element)
        element_id += 1
    
    # Top chord
    top_start = int(segments) + 2
    for i in range(int(segments)):
        element = {
            "action": "create_element",
            "params": {
                "id": element_id,
                "label": f"B{element_id}",
                "type": "beam",
                "start_node": top_start + i,
                "end_node": top_start + i + 1,
                "material_type": "steel"
            }
        }
        elements.append(element)
        element_id += 1
    
    # Verticals and diagonals
    for i in range(int(segments) + 1):
        # Vertical
        element = {
            "action": "create_element",
            "params": {
                "id": element_id,
                "label": f"V{element_id}",
                "type": "beam",
                "start_node": i + 1,
                "end_node": top_start + i,
                "material_type": "steel"
            }
        }
        elements.append(element)
        element_id += 1
        
        # Diagonal (except for the last segment)
        if i < int(segments):
            element = {
                "action": "create_element",
                "params": {
                    "id": element_id,
                    "label": f"D{element_id}",
                    "type": "beam",
                    "start_node": i + 1,
                    "end_node": top_start + i + 1,
                    "material_type": "steel"
                }
            }
            elements.append(element)
            element_id += 1
    
    actions.extend(elements)
    return actions

def clear_model(model_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Clear all nodes and elements from the model"""
    return [{
        "action": "clear_model",
        "params": {}
    }]

def set_material(model_data: Dict[str, Any], material_type: str) -> List[Dict[str, Any]]:
    """Set the material type for future elements"""
    return [{
        "action": "set_material",
        "params": {
            "material_type": material_type
        }
    }]

def process_nlp_action(parsed_action: Dict[str, Any], model_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process a parsed NLP action and return the corresponding model actions"""
    action_type = parsed_action["action"]
    params = parsed_action["params"]
    
    # Map action types to functions
    action_functions = {
        "create_multi_story_building": create_multi_story_building,
        "create_frame": create_frame,
        "create_grid": create_grid,
        "create_node": create_node,
        "create_beam": create_beam,
        "create_column": create_column,
        "create_truss": create_truss,
        "clear_model": clear_model,
        "set_material": set_material
    }
    
    if action_type in action_functions:
        return action_functions[action_type](model_data, **params)
    
    # Unknown action
    return [{
        "action": "error",
        "params": {
            "message": f"Unknown action: {action_type}"
        }
    }]

@router.post("/process", response_model=NLPResponse)
async def process_prompt(
    prompt_data: NLPPrompt,
    current_user: dict = Depends(get_current_user)
):
    # Get the model data
    model_data = get_model_by_id(prompt_data.project_id, prompt_data.model_id, current_user["id"])
    if not model_data:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Parse the prompt
    parsed_action = parse_prompt(prompt_data.prompt)
    
    if parsed_action["action"] == "unknown":
        return {
            "actions": [],
            "message": f"I couldn't understand what you want to do. Please try a different prompt.",
            "success": False
        }
    
    # Process the action
    actions = process_nlp_action(parsed_action, model_data)
    
    # Check for errors
    errors = [a for a in actions if a["action"] == "error"]
    if errors:
        return {
            "actions": [],
            "message": errors[0]["params"]["message"],
            "success": False
        }
    
    # Return the actions
    action_type = parsed_action["action"]
    action_description = action_type.replace("_", " ").capitalize()
    
    return {
        "actions": actions,
        "message": f"Successfully processed: {action_description}",
        "success": True
    }