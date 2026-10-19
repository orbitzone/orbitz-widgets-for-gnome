"""iCloud credentials stored exclusively in the desktop Secret Service."""

class Vault:
    """Passwords live exclusively in the desktop Secret Service."""
    def _service(self):
        import gi
        gi.require_version('Secret','1');from gi.repository import Secret
        schema=Secret.Schema.new('io.orbitz.Calendar.iCloud',Secret.SchemaFlags.NONE,{'account':Secret.SchemaAttributeType.STRING})
        return Secret,schema
    def put(self,identity,password):
        Secret,schema=self._service()
        if not Secret.password_store_sync(schema,{'account':identity},Secret.COLLECTION_DEFAULT,'Orbitz · Calendário iCloud',password,None):
            raise ValueError('Não foi possível guardar a senha no cofre do sistema.')
    def get(self,identity):
        Secret,schema=self._service();password=Secret.password_lookup_sync(schema,{'account':identity},None)
        if not password:raise ValueError('A senha do calendário não está disponível no cofre. Desbloqueie o cofre ou reconecte a conta.')
        return password
    def delete(self,identity):
        Secret,schema=self._service();Secret.password_clear_sync(schema,{'account':identity},None)


class ProviderVault:
    """OAuth/PAT material stays in a separate Secret Service schema, never JSON caches."""
    def _service(self):
        import gi
        gi.require_version('Secret','1')
        from gi.repository import Secret
        schema=Secret.Schema.new('io.orbitz.Calendar.Provider',Secret.SchemaFlags.NONE,
                                 {'account':Secret.SchemaAttributeType.STRING,'provider':Secret.SchemaAttributeType.STRING})
        return Secret,schema

    def _attributes(self,provider,identity):
        import re
        from calendar_events import CalendarError
        if provider not in ('google','calendly') or not isinstance(identity,str) or not re.fullmatch(provider+r'-[0-9a-f]{64}',identity):
            raise CalendarError('Identidade da credencial inválida.')
        return dict(provider=provider,account=identity)

    def put(self,provider,identity,payload):
        import json
        from calendar_events import CalendarError
        attributes=self._attributes(provider,identity)
        if not isinstance(payload,dict):raise CalendarError('Credencial do provedor inválida.')
        value=json.dumps(payload,ensure_ascii=False)
        if len(value)>65536:raise CalendarError('Credencial do provedor excede o limite.')
        Secret,schema=self._service()
        try:
            if not Secret.password_store_sync(schema,attributes,Secret.COLLECTION_DEFAULT,'Orbitz · Calendário '+provider,value,None):raise ValueError()
        except Exception:raise CalendarError('Não foi possível guardar a autorização no cofre do sistema.') from None

    def get(self,provider,identity):
        import json
        from calendar_events import CalendarError
        attributes=self._attributes(provider,identity);Secret,schema=self._service()
        try:
            value=Secret.password_lookup_sync(schema,attributes,None)
            if not value or len(value)>65536:raise ValueError()
            result=json.loads(value)
            if not isinstance(result,dict):raise ValueError()
            return result
        except Exception:raise CalendarError('Autorização indisponível no cofre; desbloqueie-o ou reconecte a conta.') from None

    def delete(self,provider,identity):
        from calendar_events import CalendarError
        attributes=self._attributes(provider,identity);Secret,schema=self._service()
        try:Secret.password_clear_sync(schema,attributes,None)
        except Exception:raise CalendarError('Não foi possível remover a autorização do cofre.') from None
