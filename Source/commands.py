class PMBusCommand:
    def __init__(self, code, name="", size=1, type="Read Byte"):
        self.code = code
        self.name = name
        self.size = size
        self.type = type

    def __repr__(self):
        return f"<PMBusCommand {self.name} (0x{self.code:02X}, {self.type}, {self.size}B)>"


# --- Basic Commands ---
CLEAR_FAULTS        = PMBusCommand(0x03, "CLEAR_FAULTS", 0, "Send Byte")
CAPABILITY          = PMBusCommand(0x19, "CAPABILITY", 1, "Read Byte")
QUERY               = PMBusCommand(0x1A, "QUERY", 1, "Block Read")
VOUT_MODE           = PMBusCommand(0x20, "VOUT_MODE", 1, "Read Byte")

# --- Fault / Warning Limits ---
VOUT_OV_FAULT_LIMIT = PMBusCommand(0x40, "VOUT_OV_FAULT_LIMIT", 2, "Read Word")
VOUT_UV_FAULT_LIMIT = PMBusCommand(0x44, "VOUT_UV_FAULT_LIMIT", 2, "Read Word")
IOUT_OC_FAULT_LIMIT = PMBusCommand(0x46, "IOUT_OC_FAULT_LIMIT", 2, "Read Word")
IOUT_OC_WARN_LIMIT  = PMBusCommand(0x4A, "IOUT_OC_WARN_LIMIT", 2, "Read Word")
OT_FAULT_LIMIT      = PMBusCommand(0x4F, "OT_FAULT_LIMIT", 2, "Read Word")
OT_WARN_LIMIT       = PMBusCommand(0x51, "OT_WARN_LIMIT", 2, "Read Word")
VIN_OV_FAULT_LIMIT  = PMBusCommand(0x55, "VIN_OV_FAULT_LIMIT", 2, "Read Word")
VIN_OV_WARN_LIMIT   = PMBusCommand(0x57, "VIN_OV_WARN_LIMIT", 2, "Read Word")
VIN_UV_WARN_LIMIT   = PMBusCommand(0x58, "VIN_UV_WARN_LIMIT", 2, "Read Word")
VIN_UV_FAULT_LIMIT  = PMBusCommand(0x59, "VIN_UV_FAULT_LIMIT", 2, "Read Word")

# --- Status Registers ---
STATUS_BYTE         = PMBusCommand(0x78, "STATUS_BYTE", 1, "Read Byte")
STATUS_WORD         = PMBusCommand(0x79, "STATUS_WORD", 2, "Read Word")
STATUS_VOUT         = PMBusCommand(0x7A, "STATUS_VOUT", 1, "Read Byte")
STATUS_IOUT         = PMBusCommand(0x7B, "STATUS_IOUT", 1, "Read Byte")
STATUS_INPUT        = PMBusCommand(0x7C, "STATUS_INPUT", 1, "Read Byte")
STATUS_TEMPERATURE  = PMBusCommand(0x7D, "STATUS_TEMPERATURE", 1, "Read Byte")
STATUS_OTHER        = PMBusCommand(0x7F, "STATUS_OTHER", 1, "Read Byte")

# --- READ_xxx ---
READ_VIN_TYPE       = PMBusCommand(0x80, "READ_VIN_TYPE", 1, "Read Byte")
STATUS_FANS_1_2     = PMBusCommand(0x81, "STATUS_FANS_1_2", 1, "Read Byte")
READ_VSB_OUT        = PMBusCommand(0x84, "READ_VSB_OUT", 2, "Read Word")
READ_ISB_OUT        = PMBusCommand(0x85, "READ_ISB_OUT", 2, "Read Word")
READ_EIN            = PMBusCommand(0x86, "READ_EIN", 6, "Block Read")
READ_EOUT           = PMBusCommand(0x87, "READ_EOUT", 6, "Block Read")
READ_VIN            = PMBusCommand(0x88, "READ_VIN", 2, "Read Word")
READ_IIN            = PMBusCommand(0x89, "READ_IIN", 2, "Read Word")
READ_VOUT           = PMBusCommand(0x8B, "READ_VOUT", 2, "Read Word")
READ_IOUT           = PMBusCommand(0x8C, "READ_IOUT", 2, "Read Word")
READ_TEMPERATURE_1  = PMBusCommand(0x8D, "READ_TEMPERATURE_1", 2, "Read Word")
READ_TEMPERATURE_2  = PMBusCommand(0x8E, "READ_TEMPERATURE_2", 2, "Read Word")
READ_TEMPERATURE_3  = PMBusCommand(0x8F, "READ_TEMPERATURE_3", 2, "Read Word")
READ_FAN_SPEED_1    = PMBusCommand(0x90, "READ_FAN_SPEED_1", 2, "Read Word")
READ_POUT           = PMBusCommand(0x96, "READ_POUT", 2, "Read Word")
READ_PIN            = PMBusCommand(0x97, "READ_PIN", 2, "Read Word")
READ_LSB            = PMBusCommand(0xB2, "READ_LSB", 2, "Read Word")
#READ_VSB            = PMBusCommand(0xB9, "READ_VSB", 2, "Read Word")
#READ_ISB            = PMBusCommand(0xBA, "READ_ISB", 2, "Read Word")
READ_FAN_DUTY       = PMBusCommand(0xBB, "READ_FAN_DUTY", 2, "Read Word")

READ_PSON       = PMBusCommand(0xB3, "READ_PSON", 1, "Read Byte")
READ_CRB      = PMBusCommand(0xB4, "READ_CRB", 1, "Read Byte")
READ_VINOK      = PMBusCommand(0xB5, "READ_VINOK", 1, "Read Byte")
READ_ALERT      = PMBusCommand(0xB7, "READ_ALERT", 1, "Read Byte")
READ_ADDR     = PMBusCommand(0xB8, "READ_ADDR", 1, "Read Byte")

# --- MFR (Manufacturer Specific) ---
PMBUS_REVISION      = PMBusCommand(0x98, "PMBUS_REVISION", 1, "Read Byte")
MFR_ID              = PMBusCommand(0x99, "MFR_ID", 8, "Block Read")
MFR_MODEL           = PMBusCommand(0x9A, "MFR_MODEL", 15, "Block Read")
MFR_REVISION        = PMBusCommand(0x9B, "MFR_REVISION", 6, "Block Read")
MFR_VIN_MIN         = PMBusCommand(0xA0, "MFR_VIN_MIN", 2, "Read Word")
MFR_VIN_MAX         = PMBusCommand(0xA1, "MFR_VIN_MAX", 2, "Read Word")
MFR_VOUT_MIN        = PMBusCommand(0xA4, "MFR_VOUT_MIN", 2, "Read Word")
MFR_VOUT_MAX        = PMBusCommand(0xA5, "MFR_VOUT_MAX", 2, "Read Word")
MFR_IOUT_MAX        = PMBusCommand(0xA6, "MFR_IOUT_MAX", 2, "Read Word")
