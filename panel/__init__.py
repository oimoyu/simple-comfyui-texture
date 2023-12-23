from .setting import classes as setting_classes
from .op import classes as op_classes
from .panel import classes as panel_classes
from .workflow_list import classes as workflow_list_classes

import bpy

classes = workflow_list_classes + setting_classes + op_classes + panel_classes
