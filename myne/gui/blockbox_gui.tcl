#!/bin/sh
# the next line restarts using wish\
exec wish "$0" "$@" 

if {![info exists vTcl(sourcing)]} {

    # Provoke name search
    catch {package require bogus-package-name}
    set packageNames [package names]

    package require Tk
    switch $tcl_platform(platform) {
    windows {
            option add *Button.padY 0
    }
    default {
            option add *Scrollbar.width 10
            option add *Scrollbar.highlightThickness 0
            option add *Scrollbar.elementBorderWidth 2
            option add *Scrollbar.borderWidth 2
    }
    }
    
}

#############################################################################
# Visual Tcl v1.60 Project
#


#################################
# VTCL LIBRARY PROCEDURES
#

if {![info exists vTcl(sourcing)]} {
#############################################################################
## Library Procedure:  Window

proc ::Window {args} {
    ## This procedure may be used free of restrictions.
    ##    Exception added by Christian Gavin on 08/08/02.
    ## Other packages and widget toolkits have different licensing requirements.
    ##    Please read their license agreements for details.

    global vTcl
    foreach {cmd name newname} [lrange $args 0 2] {}
    set rest    [lrange $args 3 end]
    if {$name == "" || $cmd == ""} { return }
    if {$newname == ""} { set newname $name }
    if {$name == "."} { wm withdraw $name; return }
    set exists [winfo exists $newname]
    switch $cmd {
        show {
            if {$exists} {
                wm deiconify $newname
            } elseif {[info procs vTclWindow$name] != ""} {
                eval "vTclWindow$name $newname $rest"
            }
            if {[winfo exists $newname] && [wm state $newname] == "normal"} {
                vTcl:FireEvent $newname <<Show>>
            }
        }
        hide    {
            if {$exists} {
                wm withdraw $newname
                vTcl:FireEvent $newname <<Hide>>
                return}
        }
        iconify { if $exists {wm iconify $newname; return} }
        destroy { if $exists {destroy $newname; return} }
    }
}
#############################################################################
## Library Procedure:  vTcl:DefineAlias

proc ::vTcl:DefineAlias {target alias widgetProc top_or_alias cmdalias} {
    ## This procedure may be used free of restrictions.
    ##    Exception added by Christian Gavin on 08/08/02.
    ## Other packages and widget toolkits have different licensing requirements.
    ##    Please read their license agreements for details.

    global widget
    set widget($alias) $target
    set widget(rev,$target) $alias
    if {$cmdalias} {
        interp alias {} $alias {} $widgetProc $target
    }
    if {$top_or_alias != ""} {
        set widget($top_or_alias,$alias) $target
        if {$cmdalias} {
            interp alias {} $top_or_alias.$alias {} $widgetProc $target
        }
    }
}
#############################################################################
## Library Procedure:  vTcl:DoCmdOption

proc ::vTcl:DoCmdOption {target cmd} {
    ## This procedure may be used free of restrictions.
    ##    Exception added by Christian Gavin on 08/08/02.
    ## Other packages and widget toolkits have different licensing requirements.
    ##    Please read their license agreements for details.

    ## menus are considered toplevel windows
    set parent $target
    while {[winfo class $parent] == "Menu"} {
        set parent [winfo parent $parent]
    }

    regsub -all {\%widget} $cmd $target cmd
    regsub -all {\%top} $cmd [winfo toplevel $parent] cmd

    uplevel #0 [list eval $cmd]
}
#############################################################################
## Library Procedure:  vTcl:FireEvent

proc ::vTcl:FireEvent {target event {params {}}} {
    ## This procedure may be used free of restrictions.
    ##    Exception added by Christian Gavin on 08/08/02.
    ## Other packages and widget toolkits have different licensing requirements.
    ##    Please read their license agreements for details.

    ## The window may have disappeared
    if {![winfo exists $target]} return
    ## Process each binding tag, looking for the event
    foreach bindtag [bindtags $target] {
        set tag_events [bind $bindtag]
        set stop_processing 0
        foreach tag_event $tag_events {
            if {$tag_event == $event} {
                set bind_code [bind $bindtag $tag_event]
                foreach rep "\{%W $target\} $params" {
                    regsub -all [lindex $rep 0] $bind_code [lindex $rep 1] bind_code
                }
                set result [catch {uplevel #0 $bind_code} errortext]
                if {$result == 3} {
                    ## break exception, stop processing
                    set stop_processing 1
                } elseif {$result != 0} {
                    bgerror $errortext
                }
                break
            }
        }
        if {$stop_processing} {break}
    }
}
#############################################################################
## Library Procedure:  vTcl:Toplevel:WidgetProc

proc ::vTcl:Toplevel:WidgetProc {w args} {
    ## This procedure may be used free of restrictions.
    ##    Exception added by Christian Gavin on 08/08/02.
    ## Other packages and widget toolkits have different licensing requirements.
    ##    Please read their license agreements for details.

    if {[llength $args] == 0} {
        ## If no arguments, returns the path the alias points to
        return $w
    }
    set command [lindex $args 0]
    set args [lrange $args 1 end]
    switch -- [string tolower $command] {
        "setvar" {
            foreach {varname value} $args {}
            if {$value == ""} {
                return [set ::${w}::${varname}]
            } else {
                return [set ::${w}::${varname} $value]
            }
        }
        "hide" - "show" {
            Window [string tolower $command] $w
        }
        "showmodal" {
            ## modal dialog ends when window is destroyed
            Window show $w; raise $w
            grab $w; tkwait window $w; grab release $w
        }
        "startmodal" {
            ## ends when endmodal called
            Window show $w; raise $w
            set ::${w}::_modal 1
            grab $w; tkwait variable ::${w}::_modal; grab release $w
        }
        "endmodal" {
            ## ends modal dialog started with startmodal, argument is var name
            set ::${w}::_modal 0
            Window hide $w
        }
        default {
            uplevel $w $command $args
        }
    }
}
#############################################################################
## Library Procedure:  vTcl:WidgetProc

proc ::vTcl:WidgetProc {w args} {
    ## This procedure may be used free of restrictions.
    ##    Exception added by Christian Gavin on 08/08/02.
    ## Other packages and widget toolkits have different licensing requirements.
    ##    Please read their license agreements for details.

    if {[llength $args] == 0} {
        ## If no arguments, returns the path the alias points to
        return $w
    }

    set command [lindex $args 0]
    set args [lrange $args 1 end]
    uplevel $w $command $args
}
#############################################################################
## Library Procedure:  vTcl:toplevel

proc ::vTcl:toplevel {args} {
    ## This procedure may be used free of restrictions.
    ##    Exception added by Christian Gavin on 08/08/02.
    ## Other packages and widget toolkits have different licensing requirements.
    ##    Please read their license agreements for details.
    uplevel #0 eval toplevel $args
    set target [lindex $args 0]
    namespace eval ::$target {set _modal 0}
}
}


if {[info exists vTcl(sourcing)]} {

proc vTcl:project:info {} {
    set base .top32
    namespace eval ::widgets::$base {
        set set,origin 1
        set set,size 1
        set runvisible 1
    }
    namespace eval ::widgets_bindings {
        set tagslist _TopLevel
    }
    namespace eval ::vTcl::modules::main {
        set procs {
        }
        set compounds {
        }
        set projectType single
    }
}
}

#################################
# USER DEFINED PROCEDURES
#

#################################
# VTCL GENERATED GUI PROCEDURES
#

proc vTclWindow. {base} {
    if {$base == ""} {
        set base .
    }
    ###################
    # CREATING WIDGETS
    ###################
    wm focusmodel $top passive
    wm geometry $top 200x200+22+29; update
    wm maxsize $top 1028 746
    wm minsize $top 111 1
    wm overrideredirect $top 0
    wm resizable $top 1 1
    wm withdraw $top
    wm title $top "page"
    bindtags $top "$top Page all"
    vTcl:FireEvent $top <<Create>>
    wm protocol $top WM_DELETE_WINDOW "vTcl:FireEvent $top <<DeleteWindow>>"

    ###################
    # SETTING GEOMETRY
    ###################

    vTcl:FireEvent $base <<Ready>>
}

proc vTclWindow.top32 {base} {
    if {$base == ""} {
        set base .top32
    }
    if {[winfo exists $base]} {
        wm deiconify $base; return
    }
    set top $base
    ###################
    # CREATING WIDGETS
    ###################
    vTcl:toplevel $top -class Toplevel \
        -menu "$top.m33" 
    wm focusmodel $top passive
    wm geometry $top 849x540+69+55; update
    wm maxsize $top 1028 726
    wm minsize $top 111 1
    wm overrideredirect $top 0
    wm resizable $top 1 1
    wm deiconify $top
    wm title $top "New Toplevel 1"
    vTcl:DefineAlias "$top" "Toplevel1" vTcl:Toplevel:WidgetProc "" 1
    bindtags $top "$top Toplevel all _TopLevel"
    vTcl:FireEvent $top <<Create>>
    wm protocol $top WM_DELETE_WINDOW "vTcl:FireEvent $top <<DeleteWindow>>"

    menu $top.m33 \
        -activeborderwidth 1 -borderwidth 1 -cursor {} -font {?s????? 9} 
    $top.m33 add command \
        -command TODO -label {New command} 
    canvas $top.can34 \
        -borderwidth 2 -closeenough 1.0 -height 563 -relief ridge -width 866 
    vTcl:DefineAlias "$top.can34" "Canvas1" vTcl:WidgetProc "Toplevel1" 1
    ttk::progressbar $top.can34.tPr36
    vTcl:DefineAlias "$top.can34.tPr36" "TProgressbar1" vTcl:WidgetProc "Toplevel1" 1
    vTcl::widgets::ttk::scrolledtext::CreateCmd $top.can34.scr37 \
        -width 125 -height 75 
    vTcl:DefineAlias "$top.can34.scr37" "Scrolledtext1" vTcl:WidgetProc "Toplevel1" 1

    .top32.can34.scr37.01 configure -background white \
        -height 3 \
        -width 10 \
        -xscrollcommand ".top32.can34.scr37.02 set" \
        -yscrollcommand ".top32.can34.scr37.03 set"
    text $top.can34.tex38 \
        -background white -width 514 -wrap none 
    vTcl:DefineAlias "$top.can34.tex38" "Text1" vTcl:WidgetProc "Toplevel1" 1
    button $top.can34.but39 \
        -pady 0 -text Send 
    vTcl:DefineAlias "$top.can34.but39" "sendmsg" vTcl:WidgetProc "Toplevel1" 1
    vTcl::widgets::ttk::scrolledtext::CreateCmd $top.can34.scr40 \
        -width 125 -height 75 
    vTcl:DefineAlias "$top.can34.scr40" "worldlist" vTcl:WidgetProc "Toplevel1" 1

    .top32.can34.scr40.01 configure -background white \
        -height 3 \
        -width 10 \
        -xscrollcommand ".top32.can34.scr40.02 set" \
        -yscrollcommand ".top32.can34.scr40.03 set"
    vTcl::widgets::ttk::scrolledtext::CreateCmd $top.can34.cpd41 \
        -width 125 -height 75 
    vTcl:DefineAlias "$top.can34.cpd41" "Scrolledtext3" vTcl:WidgetProc "Toplevel1" 1

    .top32.can34.cpd41.01 configure -background white \
        -height 3 \
        -width 10 \
        -xscrollcommand ".top32.can34.cpd41.02 set" \
        -yscrollcommand ".top32.can34.cpd41.03 set"
    frame $top.can34.fra42 \
        -borderwidth 2 -relief groove -height 135 -width 235 
    vTcl:DefineAlias "$top.can34.fra42" "Frame1" vTcl:WidgetProc "Toplevel1" 1
    set site_4_0 $top.can34.fra42
    button $site_4_0.cpd44 \
        -pady 0 -text {Stop Server} 
    vTcl:DefineAlias "$site_4_0.cpd44" "stopserver" vTcl:WidgetProc "Toplevel1" 1
    button $site_4_0.cpd45 \
        -pady 0 -text {Reboot Server} 
    vTcl:DefineAlias "$site_4_0.cpd45" "rebootserver" vTcl:WidgetProc "Toplevel1" 1
    button $site_4_0.cpd46 \
        -pady 0 -text {Start Server} 
    vTcl:DefineAlias "$site_4_0.cpd46" "startserver" vTcl:WidgetProc "Toplevel1" 1
    button $site_4_0.but47 \
        -pady 0 -text {Collect Garbage} 
    vTcl:DefineAlias "$site_4_0.but47" "gc" vTcl:WidgetProc "Toplevel1" 1
    button $site_4_0.but48 \
        -pady 0 -text {Resend Heartbeat} 
    vTcl:DefineAlias "$site_4_0.but48" "cpr" vTcl:WidgetProc "Toplevel1" 1
    button $site_4_0.but50 \
        -pady 0 -text {IRC bot reconnect} 
    vTcl:DefineAlias "$site_4_0.but50" "irc_cpr" vTcl:WidgetProc "Toplevel1" 1
    button $site_4_0.but51 \
        -pady 0 -text {Resend aList Beat} 
    vTcl:DefineAlias "$site_4_0.but51" "acpr" vTcl:WidgetProc "Toplevel1" 1
    button $site_4_0.but52 \
        -pady 0 -text {Check for Updates} 
    vTcl:DefineAlias "$site_4_0.but52" "checkupdate" vTcl:WidgetProc "Toplevel1" 1
    button $site_4_0.but53 \
        -pady 0 -text {blockBox Credits} 
    vTcl:DefineAlias "$site_4_0.but53" "credits" vTcl:WidgetProc "Toplevel1" 1
    place $site_4_0.cpd44 \
        -in $site_4_0 -x 80 -y 10 -anchor nw -bordermode inside 
    place $site_4_0.cpd45 \
        -in $site_4_0 -x 150 -y 10 -width 73 -height 19 -anchor nw \
        -bordermode inside 
    place $site_4_0.cpd46 \
        -in $site_4_0 -x 10 -y 10 -width 63 -height 19 -anchor nw \
        -bordermode inside 
    place $site_4_0.but47 \
        -in $site_4_0 -x 10 -y 40 -width 99 -height 19 -anchor nw \
        -bordermode ignore 
    place $site_4_0.but48 \
        -in $site_4_0 -x 120 -y 40 -width 99 -height 19 -anchor nw \
        -bordermode ignore 
    place $site_4_0.but50 \
        -in $site_4_0 -x 10 -y 70 -width 105 -height 19 -anchor nw \
        -bordermode ignore 
    place $site_4_0.but51 \
        -in $site_4_0 -x 120 -y 70 -width 102 -height 19 -anchor nw \
        -bordermode ignore 
    place $site_4_0.but52 \
        -in $site_4_0 -x 10 -y 100 -width 106 -height 19 -anchor nw \
        -bordermode ignore 
    place $site_4_0.but53 \
        -in $site_4_0 -x 130 -y 100 -width 91 -height 19 -anchor nw \
        -bordermode ignore 
    frame $top.can34.fra55 \
        -borderwidth 2 -relief groove -height 105 -width 595 
    vTcl:DefineAlias "$top.can34.fra55" "Frame2" vTcl:WidgetProc "Toplevel1" 1
    ###################
    # SETTING GEOMETRY
    ###################
    place $top.can34 \
        -in $top -x -10 -y -10 -width 866 -height 563 -anchor nw \
        -bordermode ignore 
    place $top.can34.tPr36 \
        -in $top.can34 -x 20 -y 530 -width 830 -height 18 -anchor nw \
        -bordermode ignore 
    place $top.can34.scr37 \
        -in $top.can34 -x 20 -y 20 -width 591 -height 363 -anchor nw \
        -bordermode ignore 
    grid columnconf $top.can34.scr37 0 -weight 1
    grid rowconf $top.can34.scr37 0 -weight 1
    place $top.can34.tex38 \
        -in $top.can34 -x 20 -y 390 -width 514 -height 19 -anchor nw \
        -bordermode ignore 
    place $top.can34.but39 \
        -in $top.can34 -x 540 -y 390 -width 69 -height 19 -anchor nw \
        -bordermode ignore 
    place $top.can34.scr40 \
        -in $top.can34 -x 620 -y 20 -width 231 -height 183 -anchor nw \
        -bordermode ignore 
    grid columnconf $top.can34.scr40 0 -weight 1
    grid rowconf $top.can34.scr40 0 -weight 1
    place $top.can34.cpd41 \
        -in $top.can34 -x 620 -y 210 -width 231 -height 173 -anchor nw \
        -bordermode inside 
    grid columnconf $top.can34.cpd41 0 -weight 1
    grid rowconf $top.can34.cpd41 0 -weight 1
    place $top.can34.fra42 \
        -in $top.can34 -x 620 -y 390 -width 235 -height 135 -anchor nw \
        -bordermode ignore 
    place $top.can34.fra55 \
        -in $top.can34 -x 20 -y 420 -width 595 -height 105 -anchor nw \
        -bordermode ignore 

    vTcl:FireEvent $base <<Ready>>
}

#############################################################################
## Binding tag:  _TopLevel

bind "_TopLevel" <<Create>> {
    if {![info exists _topcount]} {set _topcount 0}; incr _topcount
}
bind "_TopLevel" <<DeleteWindow>> {
    if {[set ::%W::_modal]} {
                vTcl:Toplevel:WidgetProc %W endmodal
            } else {
                destroy %W; if {$_topcount == 0} {exit}
            }
}
bind "_TopLevel" <Destroy> {
    if {[winfo toplevel %W] == "%W"} {incr _topcount -1}
}

Window show .
Window show .top32

