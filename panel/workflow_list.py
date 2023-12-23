import bpy


class SimpleComfyUITextureWorkflowItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    path: bpy.props.StringProperty(name="Path")


class SIMPLECOMFYUITEXTURE_UL_WORKFLOW(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.label(text=item.name)


classes = (
    SimpleComfyUITextureWorkflowItem,
    SIMPLECOMFYUITEXTURE_UL_WORKFLOW,
)
