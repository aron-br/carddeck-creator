from jinja2 import Template, Environment, FileSystemLoader

# create some test data
cards = [
    {"text1": "Text 1 Card 1", "text2": "Text 2 Card 1", "text3": "Text 3 Card 1", 'backImage':"data/code.png"},
    {"text1": "Text 1 Card 2", "text2": "Text 2 Card 2", "text3": "Text 3 Card 2", 'backImage':"data/image2.jpg"},
    {"text1": "Text 1 Card 3", "text2": "Text 2 Card 3", "text3": "Text 3 Card 3", 'backImage':"data/image3.jpg"},
] *3


# load templates folder to environment (security measure)
env = Environment(loader=FileSystemLoader('./static/templates'))

# load the `index.jinja` template
index_template = env.get_template('card_template_A4_grid.jinja')
output_from_parsed_template = index_template.render(cards=cards)

# write the parsed template
with open("./cards.html", "w") as page:
  page.write(output_from_parsed_template)