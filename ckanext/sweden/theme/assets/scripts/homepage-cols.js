(function(ckan) {
  ckan.module('homepage-cols', function($, _) {
    function ResizeIframe (el) {
      var resized = false;
      var check = ( $('iframe.twitter-timeline', el).length == 1 );
      if (check) {
        var iframe = $('iframe.twitter-timeline', el);
        if (iframe.outerHeight() > 0) {
          var height = $('.span4 .box:first', el).outerHeight()-80;
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
        $(this.el.find('.span4 .box'), this.el).matchHeight();
        ResizeIframe(this.el);
      }
    };
  });
}(window.ckan));
