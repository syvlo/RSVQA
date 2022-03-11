Data specification
=======

## Images JSON
~~~~
images{
	"id": int,
	"date_added": int,
	"original_name": str
	"sensor": str,
	"upperleft_map-x": float,
	"upperleft_map-y": float,
	"res-x": float,
	"res-y": float,
	"people_id": int,
	"type": str,
	"questions_ids": [int]
	"active": bool
}
~~~~
date_added is a time stamp
type is a string which can be "Visible", "Infrared", "Multispectral", "Hyperspectral", "Amplitude SAR", "Intensity SAR"


## Questions JSON
~~~~
questions{
	"id": int,
	"date_added": int,
	"img_id": int,
	"people_id": int,
	"type": str,
	"question": str,
	"answers_ids": [int]
	"active": bool
}
~~~~
type is the expected type of answer. Can be "yes/no", "color", "number"

## Answers JSON
~~~~
answers{
	"id": int,
	"date_added": int,
	"quesiton_id": int,
	"people_id": int,
	"answer": str,
	"active": bool
}
~~~~

## People JSON
~~~~
people{
	"id": int,
	"date_added": int,
	"login": str,
	"name": str,
	"email": str,
	"password_hash": str,
	"images": [int],
	"questions": [int],
	"answers": [int],
	"active": bool
}
~~~~