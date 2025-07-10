from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from rocrate.rocrate import ROCrate
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
    input_files: Optional[List[Any]] = None
    output_files: Optional[List[Any]] = None

@dataclass
class ProspectiveIndex:
    main_workflow: ContextEntity
    software_app: ContextEntity
    steps: List[NotebookCellProvenance]
    formal_params: Dict[str, ContextEntity]