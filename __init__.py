bl_info = {
    "name": "Object Highlight Tools (v1.2)",
    "author": "ALLAN-mfQ",
    "version": (1, 2, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > Highlight",
    "description": "Highlight selected objects with solid color and make unselected objects transparent. Original materials are safely preserved.",
    "category": "3D View",
}

import bpy
import hashlib
from bpy.app.handlers import persistent

# 翻訳辞書
translations_dict = {
    "ja_JP": {
        ("*", "Highlight"): "表示強調",
        ("*", "Selected Object Highlight"): "選択オブジェクト強調表示",
        ("*", "Make Unselected Transparent"): "未選択を半透明に",
        ("*", "Restore All Materials"): "すべてのマテリアルを復元",
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
    },
    "en_US": {
        ("*", "Highlight"): "Highlight",
        ("*", "Selected Object Highlight"): "Selected Object Highlight",
        ("*", "Make Unselected Transparent"): "Make Unselected Transparent",
        ("*", "Restore All Materials"): "Restore All Materials",
        ("*", "Transparency"): "Transparency",
        ("*", "Transparency Color"): "Transparency Color",
        ("*", "Toggle Solid Color"): "Toggle Solid Color",
        ("*", "Solid Color"): "Solid Color",
        ("*", "Show Wireframe"): "Show Wireframe",
        ("*", "Fresnel IOR"): "Fresnel IOR",
        ("*", "Use Fresnel"): "Use Fresnel",
        ("*", "Adjust transparency of unselected objects"): "Adjust transparency of unselected objects",
        ("*", "Color for transparent unselected objects"): "Color for transparent unselected objects",
        ("*", "Color for selected objects"): "Color for selected objects",
        ("*", "Show wireframe for transparent objects"): "Show wireframe for transparent objects",
        ("*", "Adjust the IOR for Fresnel effect"): "Adjust the IOR for Fresnel effect",
    }
}

TEMP_TRANSPARENCY_MAT_NAME = "Temp_Transparency_Material_OHT"
TEMP_SOLID_MAT_NAME = "Temp_Solid_Material_OHT"
BACKUP_PREFIX = "original_material_oht_"

def get_safe_key(obj_name):
    hashed = hashlib.sha1(obj_name.encode('utf-8')).hexdigest()[:16]
    return BACKUP_PREFIX + hashed

def create_temp_transparent_material():
    if TEMP_TRANSPARENCY_MAT_NAME in bpy.data.materials:
        return bpy.data.materials[TEMP_TRANSPARENCY_MAT_NAME]
    
    mat = bpy.data.materials.new(name=TEMP_TRANSPARENCY_MAT_NAME)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    output = nodes.new("ShaderNodeOutputMaterial")
    fresnel = nodes.new("ShaderNodeFresnel")
    mix_shader = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    
    mat.blend_method = 'BLEND'
    
    # ### 変更点 ### hasattrで属性の存在を確認してから設定する
    if hasattr(mat, 'shadow_method'):
        mat.shadow_method = 'NONE'
        
    update_transparency_alpha(bpy.context.scene, None)
    return mat

def create_temp_solid_material():
    if TEMP_SOLID_MAT_NAME in bpy.data.materials:
        mat = bpy.data.materials[TEMP_SOLID_MAT_NAME]
        update_solid_color(bpy.context.scene, None)
        return mat

    mat = bpy.data.materials.new(name=TEMP_SOLID_MAT_NAME)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    mat.blend_method = 'OPAQUE'
    update_solid_color(bpy.context.scene, None)
    return mat

def update_transparency_alpha(scene, depsgraph):
    if TEMP_TRANSPARENCY_MAT_NAME not in bpy.data.materials: return

    mat = bpy.data.materials[TEMP_TRANSPARENCY_MAT_NAME]
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    fresnel = next((n for n in nodes if n.type == 'FRESNEL'), None)
    mix_shader = next((n for n in nodes if n.type == 'MIX_SHADER'), None)
    transparent = next((n for n in nodes if n.type == 'BSDF_TRANSPARENT'), None)

    if not all([principled, output, fresnel, mix_shader, transparent]): return

    color = scene.transparency_color
    alpha = scene.transparency_alpha
    ior = scene.transparency_ior
    use_fresnel = scene.use_fresnel

    principled.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    principled.inputs["Alpha"].default_value = alpha
    fresnel.inputs["IOR"].default_value = ior
    transparent.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)

    for link in list(links):
        if link.to_node == output or link.to_node == mix_shader: links.remove(link)

    if use_fresnel:
        links.new(fresnel.outputs["Fac"], mix_shader.inputs["Fac"])
        links.new(principled.outputs["BSDF"], mix_shader.inputs[1])
        links.new(transparent.outputs["BSDF"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])
    else:
        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

def update_wireframe_display(scene, depsgraph):
    show_wireframe = scene.show_wireframe
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and not obj.select_get() and obj.material_slots:
            if obj.material_slots[0].material and obj.material_slots[0].material.name == TEMP_TRANSPARENCY_MAT_NAME:
                obj.show_wire = show_wireframe
                obj.show_all_edges = show_wireframe

def update_solid_color(scene, depsgraph):
    if TEMP_SOLID_MAT_NAME in bpy.data.materials:
        mat = bpy.data.materials[TEMP_SOLID_MAT_NAME]
        principled = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if principled:
            principled.inputs["Base Color"].default_value = (*scene.solid_color, 1.0)

def backup_and_set_fake_user(obj):
    key = get_safe_key(obj.name)
    if key in obj: return
    
    original_mats = []
    for slot in obj.material_slots:
        if slot.material:
            slot.material.use_fake_user = True
            original_mats.append(slot.material.name)
        else:
            original_mats.append("")
    obj[key] = original_mats

def restore_and_clear_fake_user(obj):
    key = get_safe_key(obj.name)
    if key not in obj: return False
    
    original_mat_names = obj[key]
    
    while len(obj.material_slots) < len(original_mat_names):
        obj.data.materials.append(None)
    
    for i, mat_name in enumerate(original_mat_names):
        if i < len(obj.material_slots):
            original_mat = bpy.data.materials.get(mat_name)
            obj.material_slots[i].material = original_mat
            if original_mat and original_mat.users <= 1:
                original_mat.use_fake_user = False
    
    del obj[key]
    return True

def restore_all_materials():
    restored_count = 0
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if restore_and_clear_fake_user(obj):
                restored_count += 1
            obj.show_wire = False
            obj.show_all_edges = False
    
    if restored_count > 0:
        print(f"Object Highlight Tools: Restored materials for {restored_count} object(s).")

    for mat_name in [TEMP_TRANSPARENCY_MAT_NAME, TEMP_SOLID_MAT_NAME]:
        if mat_name in bpy.data.materials:
            temp_mat = bpy.data.materials[mat_name]
            if temp_mat.users == 0:
                bpy.data.materials.remove(temp_mat)

class VIEW3D_OT_apply_transparency(bpy.types.Operator):
    bl_idname = "view3d.apply_transparency"
    bl_label = "Make Unselected Transparent"
    bl_description = "Apply transparency to unselected objects"

    def execute(self, context):
        temp_mat = create_temp_transparent_material()
        show_wireframe = context.scene.show_wireframe
        
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                if not obj.select_get():
                    backup_and_set_fake_user(obj)
                    if not obj.material_slots:
                        obj.data.materials.append(temp_mat)
                    else:
                        for slot in obj.material_slots:
                            slot.material = temp_mat
                    obj.show_wire = show_wireframe
                    obj.show_all_edges = show_wireframe
                else:
                    obj.show_wire = False
                    obj.show_all_edges = False
        return {'FINISHED'}

class VIEW3D_OT_restore_materials(bpy.types.Operator):
    bl_idname = "view3d.restore_materials"
    bl_label = "Restore All Materials"
    bl_description = "Restore original materials for all objects"

    def execute(self, context):
        restore_all_materials()
        return {'FINISHED'}

class VIEW3D_OT_toggle_solid_color(bpy.types.Operator):
    bl_idname = "view3d.toggle_solid_color"
    bl_label = "Toggle Solid Color"
    bl_description = "Toggle solid color for selected objects"

    def execute(self, context):
        if context.space_data.shading.type != 'MATERIAL':
            self.report({'WARNING'}, "Solid color only applies in Material Preview mode")
            return {'CANCELLED'}

        is_currently_solid = True
        selected_mesh_objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not selected_mesh_objs: return {'CANCELLED'}

        for obj in selected_mesh_objs:
            if not obj.material_slots or not obj.material_slots[0].material or obj.material_slots[0].material.name != TEMP_SOLID_MAT_NAME:
                is_currently_solid = False
                break
        
        if is_currently_solid:
            for obj in selected_mesh_objs:
                restore_and_clear_fake_user(obj)
        else:
            temp_mat = create_temp_solid_material()
            for obj in selected_mesh_objs:
                backup_and_set_fake_user(obj)
                if not obj.material_slots:
                    obj.data.materials.append(temp_mat)
                else:
                    for slot in obj.material_slots:
                        slot.material = temp_mat
        
        return {'FINISHED'}

class VIEW3D_PT_object_highlight_tools(bpy.types.Panel):
    bl_label = "Highlight Tools"
    bl_idname = "VIEW3D_PT_object_highlight_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Highlight"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Unselected Objects:")
        box = layout.box()
        box.operator("view3d.apply_transparency", text=bpy.app.translations.pgettext("Make Unselected Transparent"))
        box.prop(scene, "transparency_alpha", text=bpy.app.translations.pgettext("Transparency"))
        box.prop(scene, "transparency_color", text=bpy.app.translations.pgettext("Transparency Color"))
        box.prop(scene, "use_fresnel", text=bpy.app.translations.pgettext("Use Fresnel"))
        if scene.use_fresnel:
            box.prop(scene, "transparency_ior", text=bpy.app.translations.pgettext("Fresnel IOR"))
        box.prop(scene, "show_wireframe", text=bpy.app.translations.pgettext("Show Wireframe"))
        
        layout.label(text="Selected Objects:")
        box = layout.box()
        box.operator("view3d.toggle_solid_color", text=bpy.app.translations.pgettext("Toggle Solid Color"))
        box.prop(scene, "solid_color", text=bpy.app.translations.pgettext("Solid Color"))

        layout.separator()
        layout.operator("view3d.restore_materials", text=bpy.app.translations.pgettext("Restore All Materials"), icon='FILE_REFRESH')

@persistent
def restore_on_load_handler(dummy):
    restore_all_materials()

classes = [
    VIEW3D_OT_apply_transparency,
    VIEW3D_OT_restore_materials,
    VIEW3D_OT_toggle_solid_color,
    VIEW3D_PT_object_highlight_tools,
]

def register():
    bpy.app.translations.register(__name__, translations_dict)
    
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.transparency_alpha = bpy.props.FloatProperty(name="Transparency", description="Adjust transparency of unselected objects", default=0.15, min=0.0, max=1.0, update=update_transparency_alpha)
    bpy.types.Scene.transparency_color = bpy.props.FloatVectorProperty(name="Transparency Color", description="Color for transparent unselected objects", subtype='COLOR', default=(0.8, 0.8, 0.8), min=0.0, max=1.0, size=3, update=update_transparency_alpha)
    bpy.types.Scene.transparency_ior = bpy.props.FloatProperty(name="Fresnel IOR", description="Adjust the IOR for Fresnel effect", default=1.05, min=1.0, max=10.0, update=update_transparency_alpha)
    bpy.types.Scene.use_fresnel = bpy.props.BoolProperty(name="Use Fresnel", description="Enable or disable Fresnel effect", default=True, update=update_transparency_alpha)
    bpy.types.Scene.show_wireframe = bpy.props.BoolProperty(name="Show Wireframe", description="Show wireframe for transparent objects", default=True, update=update_wireframe_display)
    bpy.types.Scene.solid_color = bpy.props.FloatVectorProperty(name="Solid Color", description="Color for selected objects", subtype='COLOR', default=(0.65, 0.3, 0.35), min=0.0, max=1.0, size=3, update=update_solid_color)
    
    if restore_on_load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(restore_on_load_handler)

def unregister():
    restore_all_materials()
    
    if restore_on_load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(restore_on_load_handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.transparency_alpha
    del bpy.types.Scene.transparency_color
    del bpy.types.Scene.transparency_ior
    del bpy.types.Scene.use_fresnel
    del bpy.types.Scene.show_wireframe
    del bpy.types.Scene.solid_color
    
    bpy.app.translations.unregister(__name__)

if __name__ == "__main__":
    register()

