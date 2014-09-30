var gulp = require('gulp');
var multistream = require('multistream');
var imagemin = require('gulp-imagemin');
var less = require('gulp-less');
var changed = require('gulp-changed');
var compressor = require('gulp-compressor');

var paths = {
  src: {
    less: './assets/less/**/*',
    images: './assets/images/**/*',
    scripts: [
      './bower_components/matchHeight/jquery.matchHeight.js',
      './assets/scripts/**/*'
    ],
    fonts: './bower_components/open-sans-fontface/fonts/**/*'
  },
  dest: {
    less: './resources/styles/',
    images: './public/images/',
    scripts: './resources/scripts/',
    fonts: './resources/styles/fonts/'
  }
};

gulp.task('less', function() {
  return gulp.src(paths.src.less)
    .pipe(less())
    .pipe(compressor())
    .pipe(gulp.dest(paths.dest.less));
});

gulp.task('images', function() {
  return gulp.src(paths.src.images)
    .pipe(changed(paths.dest.images))
    .pipe(imagemin({ optimizationLevel: 5 }))
    .pipe(gulp.dest(paths.dest.images));
});

gulp.task('scripts', function() {
  return gulp.src(paths.src.scripts)
    .pipe(compressor())
    .pipe(gulp.dest(paths.dest.scripts));
});

gulp.task('fonts', function() {
  return gulp.src(paths.src.fonts)
    .pipe(gulp.dest(paths.dest.fonts));
});

gulp.task('watch', function() {
  gulp.watch(paths.src.less, ['less']);
  gulp.watch(paths.src.images, ['images']);
  gulp.watch(paths.src.scripts, ['scripts']);
});

gulp.task('default', ['less', 'images', 'scripts', 'fonts']);
