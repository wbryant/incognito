/**
 * @author wbryant
 */

$(document).ready( function() {

    // $('#table1').DataTable();
    // $('#model_reactions').DataTable();

    // All tables are DataTables and appear only when loaded
    $('table.datatable').DataTable( {
        "fnDrawCallback": function( oSettings ) {
            $('p.loader').hide();
            $(this).show();
        }
      
    });
    
    // Underline hovered links in tables 
    $('table a').hover( 
        function() {
            $( this ).css("text-decoration","underline");
        }, function() {
            $( this ).css("text-decoration","none");
        }
    );
    
    // Highlight hovered tabs in all horizontal menus 
    var previously_selected = 1;
    $(".horizontal_menu a:not('.selected')").hover(
        function() {
            previously_selected = 0;
            $( this ).addClass( "focus" );
            $( this ).siblings().css( "opacity", "0.6" );            
        },
        function() {
            $( this ).siblings().css( "opacity", "1" );
            if ( !$(this).hasClass("selected") ) {
                $( this ).removeClass( "focus" );
            }
        }
    );

    /* ################################# */
    /* # CODE FOR TABS ON RESULTS PAGE # */
    /* ################################# */
    /* Taken from http://jqueryfordesigners.com/jquery-tabs/ */
    var tabContainers = $('#tabs > div.tab'); /* Store the tabContainer; look for direct descendants that match div class */
    tabContainers.hide().filter(':first').show(); /* Hide all to start off with then show the first one */
    
    $('#tabs nav a:first').addClass( 'selected focus' );
    
    $('#tabs nav a').click(
        function () {
            
            tabContainers.hide();
            tabContainers.filter(this.hash).show();
            $( this ).siblings().removeClass( 'selected focus' );
            
            $( this ).addClass( 'selected focus' );
            return false;
        }
    );
    
   
});
