from backend.common.schema import SchemaBase


class MfaCodeParam(SchemaBase):
    code: str


class MfaSetupResult(SchemaBase):
    secret: str
    otpauth_uri: str


class MfaStatus(SchemaBase):
    enabled: bool
