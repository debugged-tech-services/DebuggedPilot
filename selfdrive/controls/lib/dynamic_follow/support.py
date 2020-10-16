class LeadData:
  v_lead = None
  x_lead = None
  a_lead = None
  status = False
  new_lead = False


class CarData:
  v_ego = 0.0
  a_ego = 0.0

  left_blinker = False
  right_blinker = False
  cruise_enabled = True


class dfData:
  v_egos = []
  v_rels = []


class dfProfiles:
  close = 0
  normal = 1
  far = 2
  auto = 3
  to_profile = {0: 'close', 1: 'normal', 2: 'far', 3: 'auto'}
  to_idx = {v: k for k, v in to_profile.items()}
