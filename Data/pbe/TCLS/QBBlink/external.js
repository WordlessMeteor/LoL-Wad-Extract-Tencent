if (window != null) {
    if (window.external == null) {
        var obj = new Object();
        window.external = obj;
        console.log('set IsMicroClient: new Obj');
    }

    if (window.external != null) {
        if (window.external.IsMicroClient == null) {
            window.external.IsMicroClient = function() {
                console.log('call IsMicroClient.');
                return 14;
            }
            console.log('set IsMicroClient success.');
        } else {
            console.log('set IsMicroClient: window.external.IsMicroClient already exist.');
        }
    } else {
        console.log('set IsMicroClient failed: window.external=null.');
    }
} else {
    console.log('set IsMicroClient failed: window=null.');
}

//alert(window.external.callcpp);
//alert(window.external.IsMicroClient);