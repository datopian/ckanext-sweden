console.log('blog-admin');

ckan.module('blog-admin', function (jQuery) {
  return {
    initialize: function () {
      console.log('blog-admin::initialize');
      jQuery('.remove-link').click(function () {
        module.confirm();
      });
    }
  };
});
