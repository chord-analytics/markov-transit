import sys
sys.path.append("/usr/src/")
from RouteModel.route import Model

db_file = '../thesis_data.db'

model = Model.from_db(db_file, 210, 1, -20, 20)
model.set_state_from_db(db_file)

print(model.current_state_int())
print(sum(model.current_state_int()))
