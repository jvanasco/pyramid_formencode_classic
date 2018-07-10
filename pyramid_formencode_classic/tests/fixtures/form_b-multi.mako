<html><head></head><body><div>
<form action="/a" method="POST">
    <% form = request.pyramid_formencode_classic.get_form("a") %>
    ${form.html_error_placeholder(formencode_form="a")|n}
    <input type="text" name="email" value="" data-formencode-form="a"/>
    <input type="text" name="username" value="" data-formencode-form="a"/>
</form>
<form action="/b" method="POST">
    <% form = request.pyramid_formencode_classic.get_form("b") %>
    ${form.html_error_placeholder(formencode_form="b")|n}
    <input type="text" name="email" value="" data-formencode-form="b"/>
    <input type="text" name="username" value="" data-formencode-form="b"/>
</form>
</div></body></html>
