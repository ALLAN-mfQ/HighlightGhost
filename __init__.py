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
    "author": "ALLAN-mfQ, 改良 by AI",
    "version": (1, 1),
    "blender": (4, 1, 0), # Blender 4.1以降で動作確認
    "location": "View3D > Sidebar > Highlight",
    "description": "Highlight selected objects with a glow while fading unselected ones like ghosts, inspired by ZBrush's Ghost Transparency",
    "category": "3D View",
}

import bpy

# 翻訳辞書 (変更なし)
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
    # en_US辞書は元のコードと同じなので省略
}


# --- 改良点: 堅牢性向上のための変更 ---
# hashlibを削除し、オブジェクト名に依存しない固定のプロパティ名を使用します。
# これにより、オブジェクト名を変更してもマテリアル情報を安全に復元できます。
BACKUP_PROPERTY_NAME = "highlight_ghost_original_materials"
TEMP_TRANSPARENCY_MAT_NAME = "Temp_Transparency_Material"
TEMP_SOLID_MAT_NAME = "Temp_Solid_Material"

# --- 改良点: コードの簡潔化 ---
# Blender 4.xを前提とし、古いバージョン用の互換性チェックを削除しました。
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

    # Material settings (Simplified for Blender 4.x)
    mat.blend_method = 'BLEND'
    mat.use_backface_culling = False
    mat.show_transparent_back = True
    mat.use_screen_refraction = False
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

# update関数群は元のままで機能するため、大きな変更はありません
def update_transparency_alpha(scene, context):
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

    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    fresnel = next((n for n in nodes if n.type == 'FRESNEL'), None)
    mix_shader = next((n for n in nodes if n.type == 'MIX_SHADER'), None)
    transparent = next((n for n in nodes if n.type == 'BSDF_TRANSPARENT'), None)

    if not all([principled, output, fresnel, mix_shader, transparent]):
        create_temp_transparent_material()
        return

    principled.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    principled.inputs["Alpha"].default_value = alpha
    fresnel.inputs["IOR"].default_value = ior
    transparent.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)

    for link in list(links):
        if link.to_node in [mix_shader, output]:
            links.remove(link)

    if use_fresnel:
        links.new(fresnel.outputs["Fac"], mix_shader.inputs["Fac"])
        links.new(principled.outputs["BSDF"], mix_shader.inputs[1])
        links.new(transparent.outputs["BSDF"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])
    else:
        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

def update_wireframe_display(scene, context):
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

def update_solid_color(scene, context):
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
        if not any(slot.material and slot.material.name == TEMP_SOLID_MAT_NAME for slot in obj.material_slots):
            return False
    return True

# --- 改良点: パフォーマンス向上のための変更 ---
def apply_transparency_to_unselected():
    """Apply transparency to unselected, VISIBLE objects to improve performance."""
    temp_mat = create_temp_transparent_material()
    shading_type = bpy.context.space_data.shading.type
    show_wireframe = bpy.context.scene.show_wireframe
    view_layer = bpy.context.view_layer

    # 処理対象を現在のビューレイヤーで表示されているオブジェクトに限定します。
    # これにより、非表示オブジェクトへの不要な処理がなくなり、パフォーマンスが向上します。
    for obj in view_layer.objects:
        if obj.type == 'MESH' and obj.visible_get(view_layer=view_layer):
            if not obj.select_get():
                # 堅牢なバックアッププロパティに元のマテリアル名を保存
                if BACKUP_PROPERTY_NAME not in obj:
                    obj[BACKUP_PROPERTY_NAME] = [slot.material.name if slot.material else "" for slot in obj.material_slots]

                if not obj.material_slots:
                    obj.data.materials.append(temp_mat)
                else:
                    for slot in obj.material_slots:
                        slot.material = temp_mat

                obj.show_wire = show_wireframe
                obj.show_all_edges = show_wireframe
                obj.display_type = 'WIRE' if show_wireframe and shading_type == 'SOLID' else 'TEXTURED'
            else:
                obj.show_wire = False
                obj.show_all_edges = False
                obj.display_type = 'TEXTURED'

    bpy.context.view_layer.update()

def apply_solid_color_to_selected():
    """Apply solid color to selected, VISIBLE objects."""
    if bpy.context.space_data.shading.type != 'MATERIAL':
        return

    temp_mat = create_temp_solid_material()
    view_layer = bpy.context.view_layer
    
    # こちらも表示されているオブジェクトのみを対象とします
    for obj in view_layer.objects:
        if obj.type == 'MESH' and obj.select_get() and obj.visible_get(view_layer=view_layer):
            # 堅牢なバックアッププロパティに元のマテリアル名を保存
            if BACKUP_PROPERTY_NAME not in obj:
                obj[BACKUP_PROPERTY_NAME] = [slot.material.name if slot.material else "" for slot in obj.material_slots]
            
            if not obj.material_slots:
                obj.data.materials.append(temp_mat)
            else:
                for slot in obj.material_slots:
                    slot.material = temp_mat

# --- 改良点: 堅牢性向上のための変更 ---
def restore_selected_materials():
    """Restore original materials for selected objects using the robust backup property."""
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH' and BACKUP_PROPERTY_NAME in obj:
            original_mat_names = obj[BACKUP_PROPERTY_NAME]
            for i, mat_name in enumerate(original_mat_names):
                if i < len(obj.material_slots):
                    if mat_name in bpy.data.materials:
                        obj.material_slots[i].material = bpy.data.materials[mat_name]
                    else:
                        obj.material_slots[i].material = None
            # バックアップ情報を削除してクリーンな状態に戻す
            del obj[BACKUP_PROPERTY_NAME]

def restore_all_materials():
    """Restore original materials for ALL objects that have a backup property."""
    # シーン内の全てのオブジェクトを走査し、非表示だったオブジェクトも確実に復元します。
    for obj in bpy.context.scene.objects:
        # バックアッププロパティを持つオブジェクトのみを対象とするため、安全かつ効率的です。
        if BACKUP_PROPERTY_NAME in obj:
            original_mat_names = obj[BACKUP_PROPERTY_NAME]
            
            # マテリアルスロット数がバックアップ時より減っている場合に対応
            num_slots_to_restore = min(len(original_mat_names), len(obj.material_slots))
            
            for i in range(num_slots_to_restore):
                mat_name = original_mat_names[i]
                if mat_name and mat_name in bpy.data.materials:
                    obj.material_slots[i].material = bpy.data.materials[mat_name]
                else:
                    obj.material_slots[i].material = None

            # バックアップ情報を削除してクリーンな状態に戻す
            del obj[BACKUP_PROPERTY_NAME]
            
            # オブジェクトの表示設定も元に戻す
            obj.show_wire = False
            obj.show_all_edges = False
            obj.display_type = 'TEXTURED'
    
    bpy.context.view_layer.update()

class VIEW3D_OT_toggle_solid_color(bpy.types.Operator):
    bl_idname = "view3d.toggle_solid_color"
    bl_label = "Toggle Solid Color"
    bl_description = "Toggle solid color for selected objects"

    def execute(self, context):
        if context.space_data.shading.type != 'MATERIAL':
            self.report({'WARNING'}, "Solid color only applies in Material Preview mode")
            return {'CANCELLED'}

        if is_selected_solid_colored():
            restore_selected_materials()
        else:
            apply_solid_color_to_selected()

        context.view_layer.update()
        return {'FINISHED'}

class VIEW3D_PT_object_highlight_tools(bpy.types.Panel):
    bl_label = "Selected Object Highlight"
    bl_idname = "VIEW3D_PT_object_highlight_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Highlight"

    def draw(self, context):
        layout = self.layout
        # 翻訳機能を利用
        pgettext = bpy.app.translations.pgettext
        
        layout.operator("view3d.apply_transparency", text=pgettext("Make Unselected Transparent"))
        layout.operator("view3d.restore_materials", text=pgettext("Restore"))
        
        col = layout.column(align=True)
        col.prop(context.scene, "transparency_alpha", text=pgettext("Transparency"))
        col.prop(context.scene, "transparency_color", text=pgettext("Transparency Color"))
        
        layout.prop(context.scene, "use_fresnel", text=pgettext("Use Fresnel"))
        if context.scene.use_fresnel:
            layout.prop(context.scene, "transparency_ior", text=pgettext("Fresnel IOR"))
        
        layout.prop(context.scene, "show_wireframe", text=pgettext("Show Wireframe"))
        
        layout.separator()
        
        layout.operator("view3d.toggle_solid_color", text=pgettext("Toggle Solid Color"))
        layout.prop(context.scene, "solid_color", text=pgettext("Solid Color"))

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
    # 翻訳登録
    # 英語辞書も明示的に含めておく
    if "en_US" not in translations_dict:
        translations_dict["en_US"] = {("*", msg): msg for msg_tuple in translations_dict["ja_JP"] for msg in msg_tuple}
    bpy.app.translations.register(__name__, translations_dict)
    
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.transparency_alpha = bpy.props.FloatProperty(
        name="Transparency", description="Adjust transparency of unselected objects",
        default=0.15, min=0.0, max=1.0, update=update_transparency_alpha
    )
    bpy.types.Scene.transparency_color = bpy.props.FloatVectorProperty(
        name="Transparency Color", description="Color for transparent unselected objects",
        subtype='COLOR', default=(0.8, 0.8, 0.8), min=0.0, max=1.0, size=3,
        update=update_transparency_alpha
    )
    bpy.types.Scene.transparency_ior = bpy.props.FloatProperty(
        name="Fresnel IOR", description="Adjust the IOR for Fresnel effect",
        default=1.05, min=1.0, max=10.0, update=update_transparency_alpha
    )
    bpy.types.Scene.use_fresnel = bpy.props.BoolProperty(
        name="Use Fresnel", description="Enable or disable Fresnel effect for transparent objects",
        default=True, update=update_transparency_alpha
    )
    bpy.types.Scene.show_wireframe = bpy.props.BoolProperty(
        name="Show Wireframe", description="Show wireframe for transparent objects",
        default=True, update=update_wireframe_display
    )
    bpy.types.Scene.solid_color = bpy.props.FloatVectorProperty(
        name="Solid Color", description="Color for selected objects",
        subtype='COLOR', default=(0.65, 0.3, 0.35), min=0.0, max=1.0, size=3,
        update=update_solid_color
    )

def unregister():
    bpy.app.translations.unregister(__name__)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.transparency_alpha
    del bpy.types.Scene.transparency_color
    del bpy.types.Scene.transparency_ior
    del bpy.types.Scene.use_fresnel
    del bpy.types.Scene.show_wireframe
    del bpy.types.Scene.solid_color

if __name__ == "__main__":
    register()
