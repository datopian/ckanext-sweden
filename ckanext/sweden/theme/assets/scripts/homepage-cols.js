this.ckan.module('homepage-cols', function($, _) {
  return {
    initialize: function () {
      $.proxyAll(this, /_on/);
      $('.span4 .box', this.el).matchHeight();
    }
  };
});
