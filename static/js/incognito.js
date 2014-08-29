/**
 * @author wbryant
 */

$(document).ready( function() {

    $('#table1').DataTable();
    $('#model_reactions').DataTable();
    
    $('table a').hover( 
        function() {
            $( this ).css("text-decoration","underline");
        }, function() {
            $( this ).css("text-decoration","none");
        }
    );

    $("#top_menu a:not('.selected')").hover(
        function() {
            $( this ).addClass( "selected" );
            $( this ).siblings( ".selected" ).css( "opacity", "0.6" );            
        }, function() {
            $( this ).removeClass( "selected" );
            $( this ).siblings( ".selected" ).css( "opacity", "1" );
        }
    );
   
} );
