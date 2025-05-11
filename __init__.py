# highlight_ghost.py
# Copyright (C) 2025 Your Name
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


bl_info = {
    "name": "HighlightGhost",
    "author": "ALLAN-mfQ",
    "version": (1, 0),
    "blender": (4, 3, 1),
    "location": "View3D > Sidebar > Highlight",
    "description": "Highlight selected objects with a glow while fading unselected ones like ghosts, inspired by ZBrush's Ghost Transparency",
    "category": "3D View",
}

import bpy
import hashlib

# 翻訳辞書
translations_dict = {
    "ja_JP": {
        ("*", "Highlight"): "表示強調",
        ("*", "Selected Object Highlight"): "選択オブジェクト強調表示",
        ("*", "Make Unselected Transparent"): "未選択を半透明に",
        ("*", "Restore"): "元に戻す",
        ("*", "Transparency"): "透明度",
        ("*", "Transparency Color"): "透明色",
        ("*", "Toggle Solid Color"): "単色化を切り替え",
        ("*", "Solid Color"): "単色",
        ("*", "Show Wireframe"): "ワイヤーフレーム表示",
        ("*", "Fresnel IOR"): "フレネル IOR",
        ("*", "Use Fresnel"): "フレネル効果を使用",
        ("*", "Adjust transparency of unselected objects"): "未選択オブジェクトの透明度を調整",
        ("*", "Color for transparent unselected objects"): "未選択オブジェクトの透明色",
        ("*", "Color for selected objects"): "選択オブジェクトの色",
        ("*", "Show wireframe for transparent objects"): "半透明オブジェクトのワイヤーフレームを表示",
        ("*", "Adjust the IOR for Fresnel effect"): "フレネル効果のIORを調整",
        ("*", "Highlight selected objects with a glow while fading unselected ones like ghosts, inspired by ZBrush's Ghost Transparency"):
            "選択オブジェクトを強調表示し、未選択オブジェクトをZBrushのゴースト表示のように透明化します",
    },
    "en_US": {
        ("*", "Highlight"): "Highlight",
        ("*", "Selected Object Highlight"): "Selected Object Highlight",
        ("*", "Make Unselected Transparent"): "Make Unselected Transparent",
        ("*", "Restore"): "Restore",
        ("*", "Transparency"): "Transparency",
        ("*", "Transparency Color"): "Transparency Color",
        ("*", "Toggle Solid Color"): "Toggle Solid Color",
        ("*", "Solid Color"): "Solid Color",
        ("*", "Show Wireframe"): "Show Wireframe",
        ("*", "Fresnel IOR"): "Fresnel IOR",
        ("*", "Use Fresnel"): "Use Fresnel",
        ("*", "Adjust transparency of unselected objects"): "Adjust transparency of unselected objects",
        ("*", "Color for transparent unselected objects"): "Color for transparent unselected ones",
        ("*", "Color for selected objects"): "Color for selected objects",
        ("*", "Show wireframe for transparent objects"): "Show wireframe for transparent objects",
        ("*", "Adjust the IOR for Fresnel effect"): "Adjust the IOR for Fresnel effect",
        ("*", "Highlight selected objects with a glow while fading unselected ones like ghosts, inspired by ZBrush's Ghost Transparency"):
            "Highlight selected objects with a glow while fading unselected ones like ghosts, inspired by ZBrush's Ghost Transparency",
    }
}

# マテリアル名
TEMP_TRANSPARENCY_MAT_NAME = "Temp_Transparency_Material"
TEMP_SOLID_MAT_NAME = "Temp_Solid_Material"
BACKUP_PREFIX = "original_material_"

def is_blender_3_or_later():
    return bpy.app.version >= (3, 0, 0)

def get_safe_key(obj_name):
    hashed = hashlib.sha1(obj_name.encode('utf-8')).hexdigest()[:16]
    return BACKUP_PREFIX + hashed

def create_temp_transparent_material():
    """Create a transparent material with all nodes, defaulting to Fresnel connections."""
    if TEMP_TRANSPARENCY_MAT_NAME in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[TEMP_TRANSPARENCY_MAT_NAME])
    
    mat = bpy.data.materials.new(name=TEMP_TRANSPARENCY_MAT_NAME)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Create nodes
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    output = nodes.new("ShaderNodeOutputMaterial")
    fresnel = nodes.new("ShaderNodeFresnel")
    mix_shader = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")

    # Node positions
    principled.location = (-400, 0)
    fresnel.location = (-70, 100)
    mix_shader.location = (100, -200)
    transparent.location = (-70, -300)
    output.location = (300, 0)

    # Node settings
    color = bpy.context.scene.transparency_color
    alpha = bpy.context.scene.transparency_alpha
    ior = bpy.context.scene.transparency_ior
    principled.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    principled.inputs["Alpha"].default_value = alpha
    fresnel.inputs["IOR"].default_value = ior
    transparent.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)

    # Default connections (Fresnel on)
    links.new(fresnel.outputs["Fac"], mix_shader.inputs["Fac"])
    links.new(principled.outputs["BSDF"], mix_shader.inputs[1])
    links.new(transparent.outputs["BSDF"], mix_shader.inputs[2])
    links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])

    # Material settings
    mat.blend_method = 'BLEND'
    mat.use_backface_culling = False
    if is_blender_3_or_later():
        if hasattr(mat, "show_transparent_back"):
            mat.show_transparent_back = True
        if hasattr(mat, "use_screen_refraction"):
            mat.use_screen_refraction = False
        if hasattr(mat, "refraction_depth"):
            mat.refraction_depth = 0.0

    return mat

def create_temp_solid_material():
    """Create or update a solid color material."""
    if TEMP_SOLID_MAT_NAME in bpy.data.materials:
        mat = bpy.data.materials[TEMP_SOLID_MAT_NAME]
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                color = bpy.context.scene.solid_color
                node.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
        return mat

    mat = bpy.data.materials.new(name=TEMP_SOLID_MAT_NAME)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    color = bpy.context.scene.solid_color
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Alpha"].default_value = 1.0
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    mat.blend_method = 'OPAQUE'

    return mat

def update_transparency_alpha(scene, depsgraph):
    """Update transparent material connections based on Fresnel toggle."""
    if TEMP_TRANSPARENCY_MAT_NAME not in bpy.data.materials:
        return

    mat = bpy.data.materials[TEMP_TRANSPARENCY_MAT_NAME]
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    color = scene.transparency_color
    alpha = scene.transparency_alpha
    ior = scene.transparency_ior
    use_fresnel = scene.use_fresnel

    # Get nodes
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    fresnel = next((n for n in nodes if n.type == 'FRESNEL'), None)
    mix_shader = next((n for n in nodes if n.type == 'MIX_SHADER'), None)
    transparent = next((n for n in nodes if n.type == 'BSDF_TRANSPARENT'), None)

    if not all([principled, output, fresnel, mix_shader, transparent]):
        create_temp_transparent_material()
        return

    # Update node values
    principled.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    principled.inputs["Alpha"].default_value = alpha
    fresnel.inputs["IOR"].default_value = ior
    transparent.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)

    # Clear existing links to Mix Shader and Output
    for link in list(links):
        if link.to_node in [mix_shader, output]:
            links.remove(link)

    # Set connections based on Fresnel toggle
    if use_fresnel:
        links.new(fresnel.outputs["Fac"], mix_shader.inputs["Fac"])
        links.new(principled.outputs["BSDF"], mix_shader.inputs[1])
        links.new(transparent.outputs["BSDF"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])
    else:
        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    # Redraw UI
    for area in bpy.context.screen.areas:
        if area.type in ('VIEW_3D', 'NODE_EDITOR'):
            area.tag_redraw()

def update_wireframe_display(scene, depsgraph):
    """Update wireframe display for transparent objects."""
    show_wireframe = scene.show_wireframe
    shading_type = bpy.context.space_data.shading.type

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and not obj.select_get():
            for slot in obj.material_slots:
                if slot.material and slot.material.name == TEMP_TRANSPARENCY_MAT_NAME:
                    obj.show_wire = show_wireframe
                    obj.show_all_edges = show_wireframe
                    obj.display_type = 'WIRE' if show_wireframe and shading_type == 'SOLID' else 'TEXTURED'

def update_solid_color(scene, depsgraph):
    """Update solid color material."""
    if TEMP_SOLID_MAT_NAME in bpy.data.materials:
        mat = bpy.data.materials[TEMP_SOLID_MAT_NAME]
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                color = scene.solid_color
                node.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)

def is_selected_solid_colored():
    """Check if selected objects have solid color material."""
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    if not selected_objects:
        return False
    for obj in selected_objects:
        if not obj.material_slots:
            return False
        for slot in obj.material_slots:
            if not slot.material or slot.material.name != TEMP_SOLID_MAT_NAME:
                return False
    return True

def apply_transparency_to_unselected():
    """Apply transparency to unselected objects."""
    temp_mat = create_temp_transparent_material()
    shading_type = bpy.context.space_data.shading.type
    show_wireframe = bpy.context.scene.show_wireframe

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            if not obj.select_get():
                key = get_safe_key(obj.name)
                if key not in obj:
                    obj[key] = [slot.material.name if slot.material else "" for slot in obj.material_slots]

                if len(obj.material_slots) == 0:
                    obj.data.materials.append(temp_mat)
                else:
                    for i in range(len(obj.material_slots)):
                        obj.material_slots[i].material = temp_mat

                obj.show_wire = show_wireframe
                obj.show_all_edges = show_wireframe
                obj.display_type = 'WIRE' if show_wireframe and shading_type == 'SOLID' else 'TEXTURED'
            else:
                obj.show_wire = False
                obj.show_all_edges = False
                obj.display_type = 'TEXTURED'

    for area in bpy.context.screen.areas:
        if area.type in ('VIEW_3D', 'NODE_EDITOR'):
            area.tag_redraw()

def apply_solid_color_to_selected():
    """Apply solid color to selected objects."""
    if bpy.context.space_data.shading.type != 'MATERIAL':
        return

    temp_mat = create_temp_solid_material()
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.select_get():
            key = get_safe_key(obj.name)
            if key not in obj:
                obj[key] = [slot.material.name if slot.material else "" for slot in obj.material_slots]
            if len(obj.material_slots) == 0:
                obj.data.materials.append(temp_mat)
            for i in range(len(obj.material_slots)):
                obj.material_slots[i].material = temp_mat

def restore_selected_materials():
    """Restore original materials for selected objects."""
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.select_get():
            key = get_safe_key(obj.name)
            if key in obj:
                original_mat_names = obj[key]
                for i, mat_name in enumerate(original_mat_names):
                    if i >= len(obj.material_slots):
                        obj.data.materials.append(None)
                    if mat_name in bpy.data.materials:
                        obj.material_slots[i].material = bpy.data.materials[mat_name]
                    else:
                        obj.material_slots[i].material = None
                del obj[key]

def restore_all_materials():
    """Restore original materials for all objects."""
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            key = get_safe_key(obj.name)
            if key in obj:
                original_mat_names = obj[key]
                for i, mat_name in enumerate(original_mat_names):
                    if i >= len(obj.material_slots):
                        obj.data.materials.append(None)
                    if mat_name in bpy.data.materials:
                        obj.material_slots[i].material = bpy.data.materials[mat_name]
                    else:
                        obj.material_slots[i].material = None
                del obj[key]
            obj.show_wire = False
            obj.show_all_edges = False
            obj.display_type = 'TEXTURED'

class VIEW3D_OT_toggle_solid_color(bpy.types.Operator):
    bl_idname = "view3d.toggle_solid_color"
    bl_label = "Toggle Solid Color"
    bl_description = "Toggle solid color for selected objects"

    def execute(self, context):
        if bpy.context.space_data.shading.type != 'MATERIAL':
            self.report({'WARNING'}, "Solid color only applies in Material Preview mode")
            return {'CANCELLED'}

        if is_selected_solid_colored():
            restore_selected_materials()
        else:
            apply_solid_color_to_selected()

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        return {'FINISHED'}

class VIEW3D_PT_object_highlight_tools(bpy.types.Panel):
    bl_label = "Selected Object Highlight"
    bl_idname = "VIEW3D_PT_object_highlight_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Highlight"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.apply_transparency", text=bpy.app.translations.pgettext("Make Unselected Transparent"))
        layout.operator("view3d.restore_materials", text=bpy.app.translations.pgettext("Restore"))
        layout.prop(context.scene, "transparency_alpha", text=bpy.app.translations.pgettext("Transparency"))
        layout.prop(context.scene, "transparency_color", text=bpy.app.translations.pgettext("Transparency Color"))
        layout.prop(context.scene, "use_fresnel", text=bpy.app.translations.pgettext("Use Fresnel"))
        if context.scene.use_fresnel:
            layout.prop(context.scene, "transparency_ior", text=bpy.app.translations.pgettext("Fresnel IOR"))
        layout.prop(context.scene, "show_wireframe", text=bpy.app.translations.pgettext("Show Wireframe"))
        layout.operator("view3d.toggle_solid_color", text=bpy.app.translations.pgettext("Toggle Solid Color"))
        layout.prop(context.scene, "solid_color", text=bpy.app.translations.pgettext("Solid Color"))

class VIEW3D_OT_apply_transparency(bpy.types.Operator):
    bl_idname = "view3d.apply_transparency"
    bl_label = "Make Unselected Transparent"
    bl_description = "Apply transparency to unselected objects"

    def execute(self, context):
        apply_transparency_to_unselected()
        return {'FINISHED'}

class VIEW3D_OT_restore_materials(bpy.types.Operator):
    bl_idname = "view3d.restore_materials"
    bl_label = "Restore"
    bl_description = "Restore original materials"

    def execute(self, context):
        restore_all_materials()
        return {'FINISHED'}

classes = [
    VIEW3D_PT_object_highlight_tools,
    VIEW3D_OT_apply_transparency,
    VIEW3D_OT_restore_materials,
    VIEW3D_OT_toggle_solid_color,
]

def register():
    # 既存の翻訳データをクリア（安全のため）
    try:
        bpy.app.translations.unregister(__name__)
    except ValueError:
        pass  # すでに登録がない場合は無視
    
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.transparency_alpha = bpy.props.FloatProperty(
        name="Transparency",
        description="Adjust transparency of unselected objects",
        default=0.15,
        min=0.0,
        max=1.0,
        update=update_transparency_alpha
    )
    bpy.types.Scene.transparency_color = bpy.props.FloatVectorProperty(
        name="Transparency Color",
        description="Color for transparent unselected objects",
        subtype='COLOR',
        default=(0.8, 0.8, 0.8),
        min=0.0,
        max=1.0,
        size=3,
        update=update_transparency_alpha
    )
    bpy.types.Scene.transparency_ior = bpy.props.FloatProperty(
        name="Fresnel IOR",
        description="Adjust the IOR for Fresnel effect",
        default=1.05,
        min=1.0,
        max=10.0,
        update=update_transparency_alpha
    )
    bpy.types.Scene.use_fresnel = bpy.props.BoolProperty(
        name="Use Fresnel",
        description="Enable or disable Fresnel effect for transparent objects",
        default=True,
        update=update_transparency_alpha
    )
    bpy.types.Scene.show_wireframe = bpy.props.BoolProperty(
        name="Show Wireframe",
        description="Show wireframe for transparent objects",
        default=True,
        update=update_wireframe_display
    )
    bpy.types.Scene.solid_color = bpy.props.FloatVectorProperty(
        name="Solid Color",
        description="Color for selected objects",
        subtype='COLOR',
        default=(0.65, 0.3, 0.35),
        min=0.0,
        max=1.0,
        size=3,
        update=update_solid_color
    )
    bpy.app.translations.register(__name__, translations_dict)
    bpy.app.handlers.depsgraph_update_post.append(update_transparency_alpha)
    bpy.app.handlers.depsgraph_update_post.append(update_wireframe_display)
    bpy.app.handlers.depsgraph_update_post.append(update_solid_color)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.transparency_alpha
    del bpy.types.Scene.transparency_color
    del bpy.types.Scene.transparency_ior
    del bpy.types.Scene.use_fresnel
    del bpy.types.Scene.show_wireframe
    del bpy.types.Scene.solid_color
    bpy.app.translations.unregister(__name__)
    bpy.app.handlers.depsgraph_update_post.remove(update_transparency_alpha)
    bpy.app.handlers.depsgraph_update_post.remove(update_wireframe_display)
    bpy.app.handlers.depsgraph_update_post.remove(update_solid_color)

if __name__ == "__main__":
    register()
