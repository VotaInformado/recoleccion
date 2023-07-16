# class DraftLaw(db.Model):  # Proyecto de ley
#     __tablename__ = "draft_law"
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(300))
#     record_number = db.Column(db.Integer)  # Acta id
#     date = db.Column(db.Date)
#     votes_affirmative = db.Column(db.Integer)
#     votes_negative = db.Column(db.Integer)
#     votes_abstention = db.Column(db.Integer)
#     votes_absent = db.Column(db.Integer)


# class VoteOption(enum.Enum):
#     AFFIRMATIVE = "A"
#     NEGATIVE = "N"
#     ABSTENTION = "O"
#     ABSENT = "P"


# class Vote(db.Model):
#     __tablename__ = "vote"
#     id = db.Column(db.Integer, primary_key=True)
#     draft_law_id = db.Column(db.Integer, db.ForeignKey("draft_law.id"))
#     person_id = db.Column(db.Integer, db.ForeignKey("person.id"))
#     vote = db.Column(db.Enum(VoteOption))