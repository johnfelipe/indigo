(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.LibraryView = Backbone.View.extend({
    el: '#library',
    template: '#search-results-template',

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      this.collection = new Indigo.Library();
      this.collection.on('change, reset', this.render, this);

      // TODO: handle search
      this.listDocuments();
    },

    listDocuments: function() {
      var collection = this.collection;
      $.getJSON('/api/documents', function(docs) {
        collection.reset(docs);
      });
    },

    render: function() {
      this.$el.html(this.template({
        count: this.collection.length,
        documents: this.collection.toJSON()
      }));
      formatTimestamps();
      this.$el.find('table').tablesorter({
        sortList: [[0, 0]],
        headers: {
          // sort timestamps as text, since they're iso8601
          4: {sorter: "text"},
        }
      });
    }
  });
})(window);
