The workflow is removed from odoo11, so I add it and change it to support odoo11, and basically this usage is just the same as it is in odoo10

in your py file just inherit model `workflow.mixin`
```
_inherit = ['workflow.mixin']
```

in your form view or list view
```
<button name='your_signal' type='workflow' string='BlaBla..'/>
```