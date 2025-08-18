{{ fullname | escape | underline }}

.. currentmodule:: {{ module }}

.. autosummary::
   :toctree: class
   :nosignatures:

{% for item in items %}
   class/{{ item }}
{% endfor %}
