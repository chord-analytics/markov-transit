from RouteModel.route import Model

# Put the path to the SQLite database here
db_file = r"C:\Users\wille\Documents\Code\mcroute\thesis_data.db"

# Now we need a route number, and a minimum and maximum state. 210 = long route, 69 = medium route, 86 = short route
# Most data sets only have a configuration = 1
model = Model.from_db(db_file, 86, 1, -10, 20)

# Now let's build some transition probability matrices
model.make_lognormal_probabilities()

model.plot_state(20)
