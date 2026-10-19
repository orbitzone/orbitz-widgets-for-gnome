"""Optional non-fiscal timesheet context, independent from invoice profiles."""
FIELDS = ('client_name','project_contract','department_costcenter')


def validate(value):
    if value is None:return {key:'' for key in FIELDS}
    if not isinstance(value,dict) or set(value)-set(FIELDS):
        raise ValueError('Contexto da timesheet inválido.')
    result = {}
    for key in FIELDS:
        item = value.get(key,'')
        if not isinstance(item,str) or len(item.strip())>200 or any(ord(c)<32 for c in item):
            raise ValueError('Campos de contexto devem ter até 200 caracteres, sem controles.')
        result[key] = item.strip()
    return result


def name(value):
    if not isinstance(value,str) or not 0<len(value.strip())<=80 or any(ord(c)<32 for c in value):
        raise ValueError('Informe o nome da timesheet, com até 80 caracteres.')
    return value.strip()
