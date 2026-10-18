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
