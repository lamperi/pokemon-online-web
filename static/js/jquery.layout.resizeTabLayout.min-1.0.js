/**
 *	UI Layout Callback: resizeTabLayout
 *
 *	Version:	1.0 - 2011-06-25
 *	Author:		Kevin Dalman (kevin.dalman@gmail.com)
 */
;(function(b){var c=b.layout;(c.callbacks||(c.callbacks={})).resizeTabLayout=function(c,e){var d=b(e.panel),a=d.data("layout");a||d.children().each(function(){if(a=b(this).data("layout"))return!1});a&&a.resizeAll()}})(jQuery);