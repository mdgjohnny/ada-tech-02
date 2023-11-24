---
title: Before the Fall
tags: [introduction]
synopsis: On how this project was built.
---
# How It All Started
In the beginning of this project, all I had was a JSON object consisting of two key-pair values: the author's name and a succinct description of the site—"a small project for ADA's course on Github and versioning."

# Project Description and Structure
The initial objective was clear enough. I had to devise a Python script capable of reading from a JSON file and seamlessly pushing its content to Github Pages. Achieving this required tight integration with Github Actions for an efficient deployment pipeline.

# Project Challenges and Thought Process
Throughout the project's creation, I encountered many challenges that demanded thoughtful consideration. Questions arose regarding the content's display, file storage, and overall folder structure. While established generators like Hugo or Jekyll were tempting options, I opted to tread the path of building my own layman generator from scratch—an exercise in practice. Admittedly, this decision came with drawbacks; given time constraints and skill limitations, the resultant code eschewed complexity, relying entirely on simple functions. These functions parsed the Markdown files, extracted their content and metadata.

Selecting Jinja2 as the template tool was an obvious first step. A brief refresher on its basics was essential. I adhered to the just-in-time learning philosophy to navigate its nuances. Before this project, I had never used Gitflow; this also meant more reading on my part.

Structuring the blog to distinguish posts from site pages necessitated careful planning. Envisioning a versatile command-line interface (CLI) for the script, featuring options like force rebuild, became pivotal, providing greater control over the deployment pipeline. The script also incorporated a rudimentary function to check directory hashes, determining whether to update based on changes or force a rebuild—an amateur yet practical addition.

As the project neared completion, I had a few uncertainties regarding the page's look and feel. Acknowledging my limitations in front-end development, I sought a minimal and simple aesthetic. With that in mind, I drew heavily from the presentation of the site <a href link="www.marginalia.nu">Marginalia.nu</a>, attempting to emulate its essence of simplicity and clarity of purpose.

Finally, this project not only serves as a technical exploration but also stands as a celebration of knowledge gained throughout the course. Embracing the principles of learning in public, documenting the journey, and gracefully embracing mistakes has been an integral part of this learning experience. As someone who's more inclined to perfectionism and stasis, actually building something, regardless of its imperfection, was a good enough reward for me.
