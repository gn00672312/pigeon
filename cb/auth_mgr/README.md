# CB Auth Manager Module

## 主要增加 PermissionRepository
- 要使用 PermissionRepository 需要在 settings 加上 FUNC_PERMISSION_CONFIG
- FUNC_PERMISSION_CONFIG 指向功能權限設定 config file
- 功能權限設定 config file 範例如下:
```
FUNC_PERMISSION = [
    ('func_user_management', 'User and Permission Management'),
    ('func_organization_management', 'Modify Organization'),
    ('func_contact_management', 'Modify Contact'),
]
```
- 可直接使用 cb_auth_mgr.decorators.func_required 控管權限
- exp: @func_required('func_user_management')
- 也可使用 django permission_required 但需要加上 app_lable
- cb_auth_mgr default app_label is 'auth_mgr'
- exp: @permission_required('auth_mgr.func_user_management')

## dev to ops
1. Engineer 開發並設定 settings.FUNC_PERMISSION_CONFIG
2. after deploy, 開啟管理介面, 系統會自動 sync settings.FUNC_PERMISSION_CONFIG
3. 權限管理員從管理介面分派權限
