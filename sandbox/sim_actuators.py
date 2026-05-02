class MockMotorController:
    """Implementación falsa del controlador de motores para el simulador."""

    # Velocidades simuladas que se aplicarán al robot
    FORWARD_SPEED = 2.0
    TURN_SPEED = 0.05
    SLOW_TURN_SPEED = 0.02
    # Velocidades por defecto (duty-cycle %)
    HIGH      = 4.0
    MID_HIGH  = 3.0
    MEDIUM    = 2.5
    MID_LOW   = 2.0
    LOW       = 1.5

    def __init__(self, calib=None):
        self.v_forward = 0.0
        self.v_lateral = 0.0
        self.v_turn = 0.0

    def _reset_speeds(self):
        self.v_forward = 0.0
        self.v_lateral = 0.0
        self.v_turn = 0.0

    def stop(self):
        self._reset_speeds()

    def adelante(self, vel=None):
        v = vel or self.HIGH
        self._reset_speeds()
        self.v_forward = v

    def atras(self, vel=None):
        v = vel or self.HIGH
        self._reset_speeds()
        self.v_forward = -v

    def lateral_derecha(self, vel=None):
        v = vel or self.MEDIUM
        self._reset_speeds()
        self.v_lateral = v

    def lateral_izquierda(self, vel=None):
        v = vel or self.MEDIUM
        self._reset_speeds()
        self.v_lateral = -v

    def girar_derecha(self, vel=None):
        v = vel or self.MEDIUM/40
        self._reset_speeds()
        self.v_turn = -v

    def girar_izquierda(self, vel=None):
        v = vel or self.MEDIUM/40
        self._reset_speeds()
        self.v_turn = v

    def girar_lento_derecha(self):
        self._reset_speeds()
        self.v_turn = -self.MID_LOW/40

    def girar_lento_izquierda(self):
        self._reset_speeds()
        self.v_turn = self.MID_LOW/40

    def cleanup(self):
        self.stop()
