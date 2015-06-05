(function(ckan) {
  ckan.module('homepage-stats', function($, _) {
    return {

      /* Default options */
      options: {
        rawdata: [],
        xaxis: {},
        yaxis: {},
        legend: {position: 'nw'},
        colors: ['#ffcc33', '#ff8844'],
        grid: {
          show: false
        },
        series: {
          lines: {
            show: true,
            lineWidth: 1
          },
          shadowSize: 0
        }
      },

      initialize: function () {
        var d1 = this.options.rawdata;
        $.plot(this.el.find(".demo-placeholder"), d1, this.options);
      }
    };
  });
}(window.ckan));
