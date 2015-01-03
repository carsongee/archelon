var count = 1;
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
            label = this.$el.find('#token-label')

            if(label.html() == 'Reveal Token') {
                label.html('Hide Token')
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
    var Commands = Backbone.Collection.extend({
        model: Command,
        url: function() {
            var base = HISTORY_API_URL;
            var query = '';
            if($('#search').val().length >= 1) {
                query = '?q=' + $('#search').val();
            }
            return base + query;
        },
        parse: function(response) {
            return response.commands;
        }
    });
            
    var CommandsView = Backbone.View.extend({
        el: '#history-table-body',
        events: {
            'click .delete-history': 'remove'
        },
        initialize: function() {
            this.listenTo(this.collection, 'sync change', this.render);
            this.collection.fetch();
        },
        render: function() {
            console.debug('Total render count: ' + count);
            count = count + 1;
            var source = $('#CommandsTemplate').html();
            var template = Handlebars.compile(source);
            var html = template(this.collection.models);
            $('#history-table').dataTable().fnDestroy();
            this.$el.html(html);
            $('#history-table').dataTable({
                'filter': false,
                'order': [[2, 'desc']],
                'pageLength': 25,
                'lengthMenu': [10, 25, 50, 75, 100, 1000],
                'columnDefs': [
                    { 'width': '60%', 'targets': 0 }
                ],
                'destroy': true
            });
        },
        remove: function(e) {
            id = $(e.currentTarget).data('id');
            this.collection.get(id).destroy();
            // Fade out and re-render once complete to update the table
            $(e.currentTarget).parent().parent().hide(400, (function(commands) {
                return function() {
                    commands.render();
                }
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
