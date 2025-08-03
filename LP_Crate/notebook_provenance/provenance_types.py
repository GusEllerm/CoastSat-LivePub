from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from rocrate.model.contextentity import ContextEntity


@dataclass
class NotebookCellProvenance:
    source: str
    howto_step: ContextEntity
    index: Optional[int] = None
    create_action: Optional[Any] = None
    prov_result: Optional[Any] = None
    control_action: Optional[Any] = None
    software_app: Optional[ContextEntity] = None
    input_params: Optional[List[Any]] = None
    output_params: Optional[List[Any]] = None
    input_files: Optional[List[ContextEntity]] = None
    output_files: Optional[List[ContextEntity]] = None
    notebook_path: Optional[str] = None
    parent_notebook: Optional[ContextEntity] = None


@dataclass
class ProspectiveIndex:
    main_workflow: ContextEntity
    software_app: ContextEntity
    steps: List[NotebookCellProvenance]
    formal_params: Dict[str, ContextEntity]