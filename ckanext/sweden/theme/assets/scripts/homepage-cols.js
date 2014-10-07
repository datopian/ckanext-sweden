(function(ckan) {
  ckan.module('homepage-cols', function($, _) {
    function ResizeIframe () {
      var resized = false;
      var check = ( $('iframe.twitter-timeline', this.el).length == 1 );
      if (check) {
        var iframe = $('iframe.twitter-timeline', this.el);
        if (iframe.outerHeight() > 0) {
          var height = $('.span4 .box:first', this.el).outerHeight()-80;
          iframe.css('height', height);
          resized = true;
        }
      }
      if (!resized) {
        setTimeout(ResizeIframe, 200);
      }
    }
    return {
      initialize: function () {
        $('.span4 .box', this.el).matchHeight();
        ResizeIframe();
      }
    };
  });
}(window.ckan));
