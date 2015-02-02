from django_assets import Bundle, register

register('css', Bundle(
    'bower_components/bootstrap/dist/css/bootstrap.min.css',
    'bower_components/bootstrap/dist/css/bootstrap-theme.min.css',
    'bower_components/fontawesome/css/font-awesome.css',
    Bundle(
        'stylesheets/app.scss',
        filters='pyscss',
        output='stylesheets/styles.%(version)s.css'),
    output='stylesheets/app.%(version)s.css'))

register('js', Bundle(
    'bower_components/jquery/dist/jquery.min.js',
    'bower_components/jquery-cookie/jquery.cookie.js',
    'bower_components/underscore/underscore-min.js',
    'bower_components/backbone/backbone.js',
    'bower_components/backbone.stickit/backbone.stickit.js',
    'bower_components/bootstrap/dist/js/bootstrap.min.js',
    'bower_components/handlebars/handlebars.min.js',
    'javascript/ace/ace.js',
    'javascript/indigo/models.js',
    'javascript/indigo/views/user.js',
    'javascript/indigo/views/reset_password.js',
    'javascript/indigo/views/document.js',
    'javascript/indigo/views/library.js',
    'javascript/indigo/views/error_box.js',
    'javascript/indigo.js',
    output='js/app.%(version)s.js'))
