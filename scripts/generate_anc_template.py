'''
A Python script that generates a template for the ANC record
from a hardcoded model.

Eventually we will have a front-end interface that will allow users
to generate this template by uploading a form image and annotating it
themselves using a GUI.
'''
from form_model import *
from json_encoder import FormTemplateEncoder
import json
from pathlib import Path


# Question 1: Is the patient less than 20 years of age?
loc_less_than_20 = Location(width=10.918688, height=11.758587, x=289.55521, y=359.28162)
resp_less_than_20 = Response("Checkbox[less_than_20]", loc_less_than_20)
less_than_20 = Question("less_than_20", QuestionType.Checkbox, [resp_less_than_20])

# Question 2: Has the patient had more than 4 prior deliveries?
loc_prior_deliveries = Location(width=11.548612, height=12.388511, x=337.8494, y=390.77783)
resp_prior_deliveries = Response("Checkbox[prior_deliveries]", loc_prior_deliveries)
prior_deliveries = Question("prior_deliveries", QuestionType.Checkbox, [resp_prior_deliveries])

# Question 3: Has the patient had a caesarean section in the past?
loc_c_section = Location(width=12.388511, height=12.80846, x=308.24295, y=469.72833)
resp_c_section = Response("Checkbox[c_section]", loc_c_section)
c_section = Question("c_section", QuestionType.Checkbox, [resp_c_section])


abs_path_to_template_image = str((Path.cwd() / "example" / "template.jpg").resolve())
f = FormTemplate("ANC_Template", abs_path_to_template_image, [less_than_20, prior_deliveries, c_section])

# Convert template to JSON and write to file
with open('anc.json', 'w') as json_file:
    json.dump(f, json_file, cls=FormTemplateEncoder, indent=4)






  # <rect
  #    style="opacity:0.7;fill:#ff6600"
  #    id="more_than_4_prior_deliveries"
  #    width="11.548612"
  #    height="12.388511"
  #    x="337.8494"
  #    y="390.77783" />

# <rect
#  style="opacity:0.7;fill:#ff6600"
#  id="edema_yes"
#  width="13.018435"
#  height="11.968561"
#  x="308.45294"
#  y="422.48401" />

# <rect
#  style="opacity:0.7;fill:#ff6600"
#  id="edema_no"
#  width="13.018435"
#  height="14.068309"
#  x="221.52338"
#  y="418.91443" />

#
# <rect
#    style="opacity:0.7;fill:#ff6600"
#    id="retained_placenta_yes"
#    width="12.388511"
#    height="13.648359"
#    x="308.03299"
#    y="516.55273" />
# <rect
#    style="opacity:0.7;fill:#ff6600"
#    id="retained_placenta_no"
#    width="14.278284"
#    height="13.22841"
#    x="221.3134"
#    y="515.08289" />
