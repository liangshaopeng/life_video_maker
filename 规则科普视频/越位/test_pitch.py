# -*- coding: utf-8 -*-
import lib_pitch as P

def test_interp_before_first_key_returns_first():
    keys = [[1.0, 0.2, 0.3], [3.0, 0.8, 0.9]]
    assert P.interp(keys, 0.0) == [0.2, 0.3]

def test_interp_after_last_key_returns_last():
    keys = [[1.0, 0.2, 0.3], [3.0, 0.8, 0.9]]
    assert P.interp(keys, 9.0) == [0.8, 0.9]

def test_interp_midpoint_is_linear():
    keys = [[0.0, 0.0, 0.0], [2.0, 1.0, 0.5]]
    assert P.interp(keys, 1.0) == [0.5, 0.25]

def test_interp_scalar_value():
    keys = [[0.0, 0.2], [4.0, 0.6]]
    assert P.interp(keys, 2.0) == [0.4]

def test_to_px_maps_normalized_to_pitch_rect():
    assert P.to_px(0.0, 0.0) == (P.X0, P.Y0)
    assert P.to_px(1.0, 1.0) == (P.X0 + P.FW, P.Y0 + P.FH)
