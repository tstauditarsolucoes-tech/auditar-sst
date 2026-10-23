package br.com.gestao.epi;

import android.content.Intent;
import android.content.ClipData;
import android.app.Activity;
import android.content.pm.ResolveInfo;
import android.content.pm.PackageManager;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.annotation.ActivityCallback;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.pdf.PdfDocument;
import android.os.CancellationSignal;
import android.os.Handler;
import android.os.Looper;
import android.os.ParcelFileDescriptor;
import android.print.PageRange;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintDocumentInfo;
import android.print.PrintManager;
import androidx.core.content.FileProvider;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Locale;
import android.net.Uri;

@CapacitorPlugin(name = "NativePrint")
public class NativePrintPlugin extends Plugin {
    private static final int PAGE_WIDTH = 595; // A4, 72 dpi
    private static final int PAGE_HEIGHT = 842;
    private static final int MARGIN = 42;
    private static final int INK = Color.rgb(26, 53, 49);
    private static final int SECONDARY = Color.rgb(66, 96, 91);
    private static final int BRAND = Color.rgb(12, 120, 101);
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private final ConcurrentHashMap<String, File> pendingSavePdf = new ConcurrentHashMap<>();

    @PluginMethod
    public void print(PluginCall call) {
        create(call, "print");
    }

    @PluginMethod
    public void sharePdf(PluginCall call) { create(call, "share"); }

    @PluginMethod
    public void savePdf(PluginCall call) { create(call, "save"); }

    private void create(PluginCall call, String action) {
        JSONObject receipt = call.getObject("receipt");
        if (receipt == null || receipt.optString("worker").trim().isEmpty()
                || (!"worker_sheet".equals(receipt.optString("documentType"))
                    && (receipt.optJSONArray("items") == null
                      || receipt.optJSONArray("items").length() == 0))) {
            call.reject("Comprovante incompleto: abra uma entrega válida antes de gerar o PDF.");
            return;
        }
        // The PDF is generated from a dedicated structured document, never from
        // the on-screen WebView. This prevents Android's blank print preview.
        new Thread(() -> {
            try {
                File directory = new File(getContext().getCacheDir(), "epi_pdfs");
                if (!directory.exists() && !directory.mkdirs()) throw new IOException("Pasta temporária indisponível");
                prune(directory);
                String id = receipt.optString("deliveryId", "entrega")
                        .replaceAll("[^A-Za-z0-9_-]", "_");
                if (id.length() > 50) id = id.substring(0, 50);
                String label = "worker_sheet".equals(receipt.optString("documentType")) ? "Ficha-Trabalhador-EPI-" : "Comprovante-EPI-";
                File output = new File(directory, label + id + "-" + System.currentTimeMillis() + ".pdf");
                int pages = generate(receipt, output);
                if (output.length() < 700) throw new IOException("PDF não foi gerado corretamente");
                final File pdf = output;
                final int pageCount = pages;
                MAIN.post(() -> {
                    try {
                        if ("share".equals(action)) {
                            try {
                                Uri uri = FileProvider.getUriForFile(getContext(),
                                    getContext().getPackageName() + ".epi_pdf_provider", pdf);
                                Intent send = new Intent(Intent.ACTION_SEND);
                                send.setType("application/pdf");
                                send.putExtra(Intent.EXTRA_STREAM, uri);
                                send.setClipData(ClipData.newUri(getContext().getContentResolver(),
                                    "Documento Gestão EPI", uri));
                                send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                                // Explicit URI grants for the receivers prevent Android OEM
                                // chooser implementations from losing content permissions.
                                List<ResolveInfo> receivers = getContext().getPackageManager()
                                    .queryIntentActivities(send, PackageManager.MATCH_DEFAULT_ONLY);
                                for (ResolveInfo receiver : receivers) {
                                    if (receiver.activityInfo != null) {
                                        getContext().grantUriPermission(receiver.activityInfo.packageName,
                                            uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
                                    }
                                }
                                Intent chooser = Intent.createChooser(send, "Compartilhar documento PDF");
                                chooser.setClipData(send.getClipData());
                                chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                                getActivity().startActivity(chooser);
                                call.resolve();
                            } catch (Exception error) {
                                call.reject("Falha ao compartilhar PDF ("+
                                    error.getClass().getSimpleName()+"): "+safeMessage(error),
                                    "PDF_SHARE_FAILED", error);
                            }
                            return;
                        } else if ("save".equals(action)) {
                            Intent document = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                            document.addCategory(Intent.CATEGORY_OPENABLE);
                            document.setType("application/pdf");
                            document.putExtra(Intent.EXTRA_TITLE, pdf.getName());
                            pendingSavePdf.put(call.getCallbackId(), pdf);
                            startActivityForResult(call, document, "onPdfSaved");
                            return;
                        } else {
                            PrintManager manager = (PrintManager) getActivity()
                                    .getSystemService(android.content.Context.PRINT_SERVICE);
                            PrintAttributes attributes = new PrintAttributes.Builder()
                                    .setMediaSize(PrintAttributes.MediaSize.ISO_A4)
                                    .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                                    .setResolution(new PrintAttributes.Resolution("pdf", "PDF", 300, 300))
                                    .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                                    .build();
                            manager.print("worker_sheet".equals(receipt.optString("documentType")) ? "Ficha de EPI do Trabalhador" : "Comprovante de Entrega de EPI",
                                    new ReadyPdfAdapter(pdf, pageCount), attributes);
                        }
                        call.resolve();
                    } catch (Exception error) {
                        call.reject("Falha ao imprimir ou salvar PDF: "+safeMessage(error), error);
                    }
                });
            } catch (Exception error) {
                MAIN.post(() -> call.reject("Falha ao gerar o PDF do comprovante: " + error.getMessage(), error));
            }
        }, "epi-pdf-export").start();
    }

    @ActivityCallback
    private void onPdfSaved(PluginCall call, ActivityResult result) {
        if (call == null) return;
        File pdf = pendingSavePdf.remove(call.getCallbackId());
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null) {
            call.reject("Salvamento cancelado.");return;
        }
        Uri destination = result.getData().getData();
        if (pdf == null || destination == null) {
            call.reject("Arquivo PDF temporário indisponível.");return;
        }
        new Thread(() -> {
            try (InputStream in = new FileInputStream(pdf);
                 OutputStream out = getContext().getContentResolver().openOutputStream(destination)) {
                if (out == null) throw new IOException("Não foi possível abrir o destino");
                byte[] buf = new byte[8192];int n;
                while ((n = in.read(buf)) >= 0) out.write(buf, 0, n);
                out.flush();
                MAIN.post(() -> call.resolve());
            } catch (Exception err) {
                MAIN.post(() -> call.reject("Falha ao salvar PDF: "+safeMessage(err), err));
            }
        }, "epi-pdf-save").start();
    }

    private static String safeMessage(Throwable error) {
        if (error == null) return "Erro desconhecido";
        String message = error.getMessage();
        return message == null || message.trim().isEmpty() ? error.getClass().getSimpleName() : message;
    }

    private static void prune(File directory) {
        File[] files = directory.listFiles();
        if (files == null) return;
        long limit = System.currentTimeMillis() - 24L * 60L * 60L * 1000L;
        for (File file : files) {
            if (file.isFile() && file.lastModified() < limit) file.delete();
        }
    }

    private static int generate(JSONObject r, File target) throws IOException {
        if ("worker_sheet".equals(r.optString("documentType"))) return generateSheet(r, target);
        PdfDocument doc = new PdfDocument();
        Writer w = new Writer(doc);
        try {
            w.title("COMPROVANTE DE ENTREGA DE EPI");
            w.paragraph("Registro eletrônico de fornecimento de Equipamentos de Proteção Individual");
            w.gap(9);
            w.section("IDENTIFICAÇÃO");
            w.field("Empresa", r.optString("company"));
            w.field("CNPJ", r.optString("cnpj"));
            w.field("Trabalhador", r.optString("worker"));
            w.field("CPF", r.optString("cpf"));
            w.field("Matrícula", r.optString("registration"));
            w.field("Função / setor", r.optString("roleSector"));
            w.field("Data / hora", r.optString("date"));
            w.field("Código do registro", r.optString("deliveryId"));
            w.gap(8);

            w.section("EQUIPAMENTOS ENTREGUES");
            JSONArray items = r.optJSONArray("items");
            for (int i = 0; i < items.length(); i++) {
                JSONObject x = items.optJSONObject(i);
                if (x == null) continue;
                String details = "CA: " + orMissing(x.optString("ca")) +
                        "  •  Modelo: " + orMissing(x.optString("model")) +
                        "  •  Tamanho: " + orMissing(x.optString("size"));
                w.itemRow(x.optString("name","EPI"), x.optString("qty","1"), details);
            }
            w.gap(7);
            w.section("REGISTRO DA ENTREGA");
            w.field("Tipo", r.optString("type"));
            w.field("Motivo", r.optString("reason"));
            w.field("Entregue por", r.optString("deliveredBy"));
            w.field("Responsável", r.optString("responsible"));
            w.field("Código da liberação", r.optString("authorizationCode"));
            w.field("Liberado por", r.optString("authorizedBy"));
            w.field("Revisão do TST", r.optString("reviewStatus"));
            w.field("Observações", r.optString("notes"));
            w.gap(8);

            w.section("DECLARAÇÃO");
            w.paragraph("Declaro que recebi os equipamentos relacionados acima e fui orientado quanto ao uso correto, conservação e comunicação de danos ou necessidade de substituição, conforme os procedimentos de segurança aplicáveis.");
            w.gap(9);
            w.section("CONFIRMAÇÃO E EVIDÊNCIAS");
            boolean facial = r.optBoolean("facial", false);
            if (facial) {
                w.field("Método", "Biometria facial verificada");
                w.field("Compatibilidade", r.optString("similarity"));
                w.field("Data / hora da verificação", r.optString("verifiedAt"));
                w.field("ID da evidência", r.optString("evidenceId").isEmpty() ? "Não registrado neste comprovante" : r.optString("evidenceId"));
                w.field("Hash da evidência", r.optString("evidenceHash"));
            } else {
                w.field("Método", r.optString("method", "Assinatura eletrônica"));
                String signature = r.optString("signature");
                if (signature.startsWith("data:image/png;base64,") ||
                        signature.startsWith("data:image/jpeg;base64,")) {
                    try {
                        byte[] data = android.util.Base64.decode(
                                signature.substring(signature.indexOf(',') + 1), android.util.Base64.DEFAULT);
                        Bitmap image = BitmapFactory.decodeByteArray(data, 0, data.length);
                        if (image != null) {
                            w.signature(image);
                            image.recycle();
                        }
                    } catch (Exception ignored) {
                        w.paragraph("Imagem da assinatura não disponível neste registro.");
                    }
                } else {
                    w.paragraph("Imagem da assinatura não disponível neste registro.");
                }
            }
            w.field("ID do comprovante", r.optString("evidenceRecordId"));
            w.field("Hash do comprovante", r.optString("receiptHash"));
            w.finish();
            try (FileOutputStream out = new FileOutputStream(target)) { doc.writeTo(out); }
            return w.pageCount;
        } finally {
            doc.close();
        }
    }


    private static int generateSheet(JSONObject r, File target) throws IOException {
        PdfDocument doc = new PdfDocument();
        Writer w = new Writer(doc);
        try {
            w.title("FICHA INDIVIDUAL DE EPI");
            w.paragraph("Histórico de fornecimento e rastreabilidade do trabalhador");
            w.gap(12);
            w.section("IDENTIFICAÇÃO DO TRABALHADOR");
            w.field("Empresa", r.optString("company"));
            w.field("CNPJ", r.optString("cnpj"));
            w.field("Nome completo", r.optString("worker"));
            w.field("CPF", r.optString("cpf"));
            w.field("Matrícula", r.optString("registration"));
            w.field("Função / setor", r.optString("roleSector"));
            w.field("Gerado em", r.optString("date"));
            w.gap(7);
            w.section("EPIs REGISTRADOS NO HISTÓRICO");
            JSONArray items = r.optJSONArray("items");
            if(items==null || items.length()==0) w.paragraph("Nenhum EPI foi localizado para o ID deste trabalhador nos dados disponíveis neste aparelho. Confira a sincronização e o cadastro antes de emitir uma ficha definitiva.");
            else for(int i=0;i<items.length();i++){
                JSONObject x=items.optJSONObject(i);if(x==null)continue;
                w.itemRow(x.optString("name","EPI"),x.optString("qty","0"),
                    "CA: "+orMissing(x.optString("ca"))+
                    "  •  Modelo: "+orMissing(x.optString("model"))+
                    "  •  Tamanho: "+orMissing(x.optString("size")));
            }
            w.section("MOVIMENTAÇÕES / ENTREGAS");
            JSONArray records=r.optJSONArray("deliveries");
            if(records==null || records.length()==0)w.paragraph("Não há entregas associadas ao ID deste trabalhador nos registros consultados neste aparelho. Não significa necessariamente ausência de entregas em outros dispositivos.");
            else for(int i=0;i<records.length();i++){
                JSONObject d=records.optJSONObject(i);if(d==null)continue;
                w.text(d.optString("date","Data não informada")+"  •  "+d.optString("type","Entrega"),11,true,INK);
                w.text(d.optString("items","EPI não informado"),10.5f,false,INK);
                w.field("Motivo",d.optString("reason"));
                w.field("Confirmado por",d.optString("method"));
                w.field("Entregue por",d.optString("deliveredBy"));
                w.field("ID da entrega",d.optString("id"));
                w.gap(10);
            }
            w.section("ORIENTAÇÕES E OBSERVAÇÕES");
            w.paragraph("Esta ficha registra as entregas disponíveis no sistema, podendo conter lançamentos históricos. Consulte devoluções e movimentações para confirmar os EPIs atualmente em posse. A ficha não substitui a conferência física e não constitui certificado de assinatura digital.");
            w.finish();
            try(FileOutputStream out=new FileOutputStream(target)){doc.writeTo(out);}
            return w.pageCount;
        } finally {doc.close();}
    }

    private static String orMissing(String value) {
        return value == null || value.trim().isEmpty() ? "Não informado" : value.trim();
    }

    private static final class Writer {
        private final PdfDocument doc;
        private final Paint ink = new Paint(Paint.ANTI_ALIAS_FLAG);
        private PdfDocument.Page page;
        private Canvas canvas;
        private float y;
        private int pageCount;
        private String documentTitle = "DOCUMENTO DE EPI";
        private final int TITLE = Color.rgb(27, 49, 46);
        private final int BG = Color.rgb(239, 248, 245);
        private final int RULE = Color.rgb(218, 232, 227);

        Writer(PdfDocument document) {
            doc = document;
            nextPage();
        }

        private void drawString(String txt, float x, float baseline, float fontSize, boolean bold, int color) {
            ink.setTypeface(Typeface.create("sans-serif",
                bold ? Typeface.BOLD : Typeface.NORMAL));
            ink.setTextSize(fontSize);
            ink.setColor(color);
            ink.setStyle(Paint.Style.FILL);
            canvas.drawText(txt, x, baseline, ink);
        }

        private void nextPage() {
            if (page != null) closePage();
            pageCount++;
            page = doc.startPage(new PdfDocument.PageInfo.Builder(PAGE_WIDTH,PAGE_HEIGHT,pageCount).create());
            canvas = page.getCanvas();
            canvas.drawColor(Color.WHITE);
            ink.setColor(Color.rgb(8, 100, 84));
            canvas.drawRect(0, 0, PAGE_WIDTH, 79, ink);
            drawString("GESTÃO EPI", MARGIN, 38, 18, true, Color.WHITE);
            drawString("CONTROLE E RASTREABILIDADE DE EQUIPAMENTOS", MARGIN, 57, 9.2f, false, Color.WHITE);
            drawString("DOCUMENTO ELETRÔNICO", PAGE_WIDTH-MARGIN-119, 38, 8, true, Color.WHITE);
            y = 109;
        }

        private void closePage() {
            if (page == null) return;
            ink.setColor(RULE);
            ink.setStrokeWidth(1);
            canvas.drawLine(MARGIN, PAGE_HEIGHT-47, PAGE_WIDTH-MARGIN, PAGE_HEIGHT-47, ink);
            drawString("Gestão EPI  •  "+documentTitle, MARGIN, PAGE_HEIGHT-30, 8.2f, false, SECONDARY);
            drawString("PÁGINA "+pageCount, PAGE_WIDTH-MARGIN-49, PAGE_HEIGHT-30, 8.2f, true, SECONDARY);
            doc.finishPage(page);
            page = null;
        }

        private void need(float height) {
            if (y+height > PAGE_HEIGHT-69) nextPage();
        }

        void finish() {closePage();}
        void gap(float amount) {need(amount);y += amount;}

        void title(String value) {
            documentTitle=value;
            text(value, 17.5f, true, TITLE);
        }

        void section(String value) {
            need(53);
            y += 10;
            float top=y-15;
            ink.setColor(BG);
            canvas.drawRoundRect(new RectF(MARGIN,top,PAGE_WIDTH-MARGIN,top+29),6,6,ink);
            ink.setColor(BRAND);
            canvas.drawRoundRect(new RectF(MARGIN,top,MARGIN+4,top+29),2,2,ink);
            drawString(value, MARGIN+14, top+19, 11.5f, true, BRAND);
            y=top+40;
        }

        void paragraph(String value) {text(value,11f,false,INK);}

        // Fields have fixed label and flowing value columns. Long IDs, names and
        // hashes wrap to a second line without clipping outside the printable area.
        void field(String name,String value) {
            if(value == null || value.trim().isEmpty())return;
            need(25);
            float previous=y;
            y += 3;
            drawString(name.toUpperCase(new Locale("pt","BR")), MARGIN+2, y, 9f, true, SECONDARY);
            float startX=MARGIN+168;
            float width=PAGE_WIDTH-MARGIN-startX-3;
            y=drawWrapped(value,startX,y,width,10.5f,INK,false,14.7f);
            y += 7;
            ink.setColor(Color.rgb(237,243,241));
            canvas.drawLine(MARGIN, y-3, PAGE_WIDTH-MARGIN,y-3,ink);
        }

        void itemRow(String name,String qty,String details) {
            need(65);
            float y0=y;
            ink.setColor(Color.rgb(247,250,249));
            canvas.drawRoundRect(new RectF(MARGIN,y0-8,PAGE_WIDTH-MARGIN,y0+50),6,6,ink);
            y=drawWrapped(name,MARGIN+12,y0+11,PAGE_WIDTH-2*MARGIN-124,12f,TITLE,true,14.8f);
            drawString("QTDE. "+qty,PAGE_WIDTH-MARGIN-90,y0+11,10.4f,true,BRAND);
            y=Math.max(y,y0+28);
            y=drawWrapped(details,MARGIN+12,y,PAGE_WIDTH-2*MARGIN-26,9.5f,SECONDARY,false,13f);
            y=Math.max(y+10,y0+62);
        }

        // Unlike the previous one-line implementation, this supports long
        // hashes, identifiers, accented names and paragraphs without clipping.
        private float drawWrapped(String source,float x,float baseline,float maxWidth,
                                  float size,int color,boolean bold,float lineHeight) {
            if(source == null)return baseline;
            ink.setTypeface(Typeface.create("sans-serif",bold?Typeface.BOLD:Typeface.NORMAL));
            ink.setTextSize(size);
            String remaining=source.replace('\r',' ').replace('\n',' ').trim();
            float current=baseline;
            while(!remaining.isEmpty()) {
                int count=remaining.length();
                while(count>1 && ink.measureText(remaining,0,count)>maxWidth)count--;
                if(count<remaining.length() && count>2) {
                    int space=remaining.lastIndexOf(' ',count);
                    if(space > Math.max(2,count/3))count=space;
                }
                String line=remaining.substring(0,count).trim();
                if(line.isEmpty())break;
                if(current>PAGE_HEIGHT-80) {
                    y=current;
                    nextPage();
                    current=y;
                }
                drawString(line,x,current,size,bold,color);
                remaining=remaining.substring(count).trim();
                current += lineHeight;
            }
            return current;
        }

        void text(String value,float size,boolean bold,int color) {
            if(value==null||value.trim().isEmpty())return;
            need(size+8);
            y=drawWrapped(value,MARGIN+2,y,PAGE_WIDTH-2*MARGIN-4,size,color,bold,size*1.42f);
            y+=3;
        }

        void signature(Bitmap image) {
            if(image==null||image.getWidth()<=0||image.getHeight()<=0)return;
            float maxW=340,maxH=84;
            float scale=Math.min(maxW/image.getWidth(),maxH/image.getHeight());
            float width=image.getWidth()*scale,height=image.getHeight()*scale;
            need(height+29);
            ink.setColor(Color.WHITE);
            canvas.drawBitmap(image,null,new RectF(MARGIN+10,y,MARGIN+10+width,y+height),ink);
            y+=height+12;
            ink.setColor(RULE);
            canvas.drawLine(MARGIN+10,y,PAGE_WIDTH-MARGIN-10,y,ink);
            y+=13;
        }
    }

    // Prints a PDF that already exists. Unlike WebView printing, the spooler
    // receives real PDF bytes, so "Salvar como PDF" cannot capture a hidden view.
    private static final class ReadyPdfAdapter extends PrintDocumentAdapter {
        private final File pdf;
        private final int pages;
        ReadyPdfAdapter(File file, int pageCount) { pdf = file; pages = pageCount; }
        @Override
        public void onLayout(PrintAttributes oldAttributes, PrintAttributes newAttributes,
                CancellationSignal signal, LayoutResultCallback callback, android.os.Bundle extras) {
            if (signal.isCanceled()) { callback.onLayoutCancelled(); return; }
            PrintDocumentInfo info = new PrintDocumentInfo.Builder(pdf.getName())
                    .setContentType(PrintDocumentInfo.CONTENT_TYPE_DOCUMENT)
                    .setPageCount(Math.max(1, pages))
                    .build();
            callback.onLayoutFinished(info, true);
        }
        @Override
        public void onWrite(PageRange[] ranges, ParcelFileDescriptor destination,
                CancellationSignal signal, WriteResultCallback callback) {
            new Thread(() -> {
                try (FileInputStream in = new FileInputStream(pdf);
                     FileOutputStream out = new FileOutputStream(destination.getFileDescriptor())) {
                    byte[] buf = new byte[8192];
                    int n;
                    while ((n = in.read(buf)) != -1) {
                        if (signal.isCanceled()) break;
                        out.write(buf, 0, n);
                    }
                    out.flush();
                    MAIN.post(() -> {
                        if (signal.isCanceled()) callback.onWriteCancelled();
                        else callback.onWriteFinished(new PageRange[]{PageRange.ALL_PAGES});
                    });
                } catch (Exception error) {
                    MAIN.post(() -> callback.onWriteFailed("Falha ao gravar o arquivo PDF"));
                } finally {
                    try { destination.close(); } catch (Exception ignored) { }
                }
            }, "epi-print-spool").start();
        }
    }
}
