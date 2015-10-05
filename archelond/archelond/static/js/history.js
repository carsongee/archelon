(function($){

  var Token = Backbone.Model.extend({
    url: TOKEN_API_URL
  });
  var TokenView = Backbone.View.extend({
    el: '#token',
    events: {
      'click #token-toggle': 'toggle'
    },
    initialize: function() {
      this.model = new Token();
      this.model.fetch();
    },
    toggle: function() {
      label = this.$el.find('#token-label');
      
      if(label.html() == 'Reveal Token') {
        label.html('Hide Token');
        $('#token-display').html(this.model.attributes.token).slideDown(400);
      } else {
        label.html('Reveal Token');
        $('#token-display').html('').slideUp(400);
      }
    }
  });

  var Command = Backbone.Model.extend({
    last_used: function() {
      return moment(new Date(this.get('timestamp'))).format(
        'hh:mm.ss.Sa MM.DD.YYYY'
      );
    },
    url: function() {
      return HISTORY_API_URL + '/' + this.get('id');
    }
  });
  var Commands = Backbone.PageableCollection.extend({
    model: Command,
    url: function() {
      var base = HISTORY_API_URL + '?o=r';
      var query = '';
      if($('#search').val().length >= 1) {
        query = '&q=' + $('#search').val();
      }
      return base + query;
    },
    state: {
      pageSize: 50,
      currentPage: 1,
      totalRecords: 1
    },
    queryParams: {
      currentPage: 'p',
      totalPages: null,
      totalRecords: null,
      order: "direction",
      directions: {
        "-1": "asc",
        "1": "desc"
      }
    },
    parseState: function (resp, queryParams, state, options) {
      if(state.currentPage == state.totalPages &&
        resp.commands.length > 0) {
        
        return {totalRecords: state.totalRecords+=50};
      }
      return {};
    },
    parseRecords: function(response) {
      return response.commands;
    }
  });
  var CommandsView = Backbone.View.extend({
    el: '#table-grid',
    events: {
      'click .delete-history': 'remove'
    },
    initialize: function() {
      this.listenTo(this.collection, 'sync change', this.render);
      this.collection.fetch();
      // Set up a grid to use the pageable collection
      var commandGrid = new Backgrid.Grid({
        className: "history-table backgrid",
        columns: [
          {
            name: "command",
            label: "Command",
            editable: false,
            sortable: false,
            cell: Backgrid.StringCell
          },
          {
            name: "host",
            label: "Host",
            editable: false,
            sortable: false,
            cell: Backgrid.StringCell
          },
          {
            name: "last_used",
            label: "Last Used",
            editable: false,
            sortable: false,
            cell: Backgrid.StringCell.extend({
              formatter: _.extend({}, Backgrid.CellFormatter.prototype, {
                fromRaw: function (rawValue, model) {
                  return model.last_used();
                }
              })
            })
          },
          {
            name: "actions",
            label: "Actions",
            editable: false,
            sortable: false,
            cell: Backgrid.StringCell.extend({
              render: function() {
                this.$el.empty();
                var model = this.model;
                var source = $('#actionTemplate').html();
                var template = Handlebars.compile(source);
                this.$el.html(template(model));
                return this;
              }
            })
          }

        ],
        collection: this.collection
      });
      var $tableGrid = $('#table-grid').append(commandGrid.render().el);
      // Initialize the paginator
      var paginator = new Backgrid.Extension.Paginator({
        collection: this.collection
      });

      // Render the paginator
      $tableGrid.before(paginator.render().el);

      this.commandGrid = commandGrid;
      
    },
    remove: function(e) {
      var id = $(e.currentTarget).data('id');
      var model = this.collection.get(id);
      // Fade out and re-render once complete to update the table
      $(e.currentTarget).parent().parent().hide(400, (function(commands) {
        return function() {
          model.destroy();
          commands.render();
        };
      })(this));
    }
  });
  var Search = Backbone.View.extend({
    el: '#search-box',
    events: {
      'keyup #search': 'search',
      'keypress #search': 'disable_enter'
    },
    disable_enter: function(event) {
      if (event.keyCode == 13) {
        event.preventDefault();
      }
    },
    search: function() {
      var newState = this.collection.state;
      newState['currentPage'] = 1;
      newState['totalRecords'] = 1;
      this.collection.fetch();
    }
  });
  var collection = new Commands();
  var commands = new CommandsView({
    'collection': collection
  });
  var search = new Search({
    'collection': collection
  });
  var token = new TokenView();
  
})(jQuery);
