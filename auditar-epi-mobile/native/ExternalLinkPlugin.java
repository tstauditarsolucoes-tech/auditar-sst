package br.com.gestao.epi;

import android.content.Intent;
import android.net.Uri;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "ExternalLink")
public class ExternalLinkPlugin extends Plugin {
    @PluginMethod
    public void openUrl(PluginCall call) {
        String url=call.getString("url","");
        Uri uri;
        try {uri=Uri.parse(url);}catch(Exception ex){call.reject("Endereço inválido.");return;}
        if(!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost()==null) {
            call.reject("Somente links HTTPS são permitidos.");return;
        }
        getActivity().runOnUiThread(() -> {
            try {
                Intent intent=new Intent(Intent.ACTION_VIEW,uri);
                intent.addCategory(Intent.CATEGORY_BROWSABLE);
                getActivity().startActivity(intent);
                call.resolve();
            } catch(Exception ex) {
                call.reject("Não foi possível abrir o navegador instalado.",ex);
            }
        });
    }
}