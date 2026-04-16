class MockMotorController:
    """Implementación falsa del controlador de motores para el simulador."""

    # Velocidades simuladas que se aplicarán al robot
    FORWARD_SPEED = 2.0
    TURN_SPEED = 0.05
    SLOW_TURN_SPEED = 0.02

    def __init__(self, calib=None):
        self.v_forward = 0.0
        self.v_turn = 0.0

    def _reset_speeds(self):
        self.v_forward = 0.0
        self.v_turn = 0.0

    def stop(self):
        self._reset_speeds()

    def adelante_lento(self):
        self._reset_speeds()
        self.v_forward = self.FORWARD_SPEED

    def atras(self, vel=None):
        self._reset_speeds()
        self.v_forward = -self.FORWARD_SPEED

    def lateral_derecha(self, vel=None):
        pass

    def lateral_izquierda(self, vel=None):
        pass

    def girar_derecha(self, vel=None):
        self._reset_speeds()
        self.v_turn = -self.TURN_SPEED

    def girar_izquierda(self, vel=None):
        self._reset_speeds()
        self.v_turn = self.TURN_SPEED

    def girar_lento_derecha(self):
        self._reset_speeds()
        self.v_turn = -self.SLOW_TURN_SPEED

    def girar_lento_izquierda(self):
        self._reset_speeds()
        self.v_turn = self.SLOW_TURN_SPEED

    def cleanup(self):
        self.stop()
