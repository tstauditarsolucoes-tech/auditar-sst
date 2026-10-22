package br.com.gestao.epi;

import android.content.Intent;
import android.content.ClipData;
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

    @PluginMethod
    public void print(PluginCall call) {
        create(call, false);
    }

    @PluginMethod
    public void sharePdf(PluginCall call) {
        create(call, true);
    }

    private void create(PluginCall call, boolean share) {
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
                        if (share) {
                            Uri uri = FileProvider.getUriForFile(getContext(),
                                    getContext().getPackageName() + ".epi_pdf_provider", pdf);
                            Intent intent = new Intent(Intent.ACTION_SEND);
                            intent.setType("application/pdf");
                            intent.putExtra(Intent.EXTRA_STREAM, uri);
                            intent.setClipData(ClipData.newUri(getContext().getContentResolver(), "Documento Gestão EPI", uri));
                            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                            Intent chooser = Intent.createChooser(intent, "Compartilhar PDF de EPI");
                            chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                            chooser.setClipData(intent.getClipData());
                            getActivity().startActivity(chooser);
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
                        call.reject(share ? "Falha ao compartilhar PDF" : "Falha ao abrir impressão", error);
                    }
                });
            } catch (Exception error) {
                MAIN.post(() -> call.reject("Falha ao gerar o PDF do comprovante: " + error.getMessage(), error));
            }
        }, "epi-pdf-export").start();
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
                String label = x.optString("name", "EPI") + "   |   Qtd.: " + x.optString("qty", "1");
                w.text(label, 12.2f, true, INK);
                String details = "CA: " + orMissing(x.optString("ca")) +
                        "   |   Modelo: " + orMissing(x.optString("model")) +
                        "   |   Tamanho: " + orMissing(x.optString("size"));
                w.text(details, 10.3f, false, SECONDARY);
                w.gap(4);
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
            if(items==null || items.length()==0) w.paragraph("Nenhum EPI consta nas entregas registradas.");
            else for(int i=0;i<items.length();i++){
                JSONObject x=items.optJSONObject(i);if(x==null)continue;
                w.text(x.optString("name","EPI"),12,true,INK);
                w.text("CA: "+orMissing(x.optString("ca"))+"  |  Modelo: "+
                    orMissing(x.optString("model"))+"  |  Tamanho: "+
                    orMissing(x.optString("size")),10,false,SECONDARY);
                w.text("Quantidade entregue no histórico: "+x.optString("qty","0"),10,false,INK);
                w.gap(5);
            }
            w.section("MOVIMENTAÇÕES / ENTREGAS");
            JSONArray records=r.optJSONArray("deliveries");
            if(records==null || records.length()==0)w.paragraph("Nenhuma entrega registrada.");
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
        private int pageCount = 0;

        Writer(PdfDocument document) {
            doc = document;
            nextPage();
        }

        private void nextPage() {
            if (page != null) closePage();
            pageCount++;
            page = doc.startPage(new PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, pageCount).create());
            canvas = page.getCanvas();
            canvas.drawColor(Color.WHITE);
            y = MARGIN + 12;
            ink.setColor(BRAND);
            ink.setStrokeWidth(2.6f);
            canvas.drawLine(MARGIN, 32, PAGE_WIDTH - MARGIN, 32, ink);
            ink.setStrokeWidth(1);
        }

        private void closePage() {
            if (page == null) return;
            ink.setTypeface(Typeface.DEFAULT);
            ink.setTextSize(8);
            ink.setColor(SECONDARY);
            canvas.drawText("Gestão EPI - comprovante eletrônico", MARGIN, PAGE_HEIGHT - 24, ink);
            canvas.drawText("Página " + pageCount, PAGE_WIDTH - MARGIN - 47, PAGE_HEIGHT - 24, ink);
            doc.finishPage(page);
            page = null;
        }

        void finish() { closePage(); }
        void gap(float amount) { need(amount); y += amount; }
        void title(String t) { text(t, 19, true, BRAND); }
        void section(String t) {
            need(48);
            gap(10);
            float top = y - 15f;
            ink.setColor(Color.rgb(234, 247, 243));
            canvas.drawRoundRect(new RectF(MARGIN - 8, top, PAGE_WIDTH - MARGIN + 8, top + 29), 6f, 6f, ink);
            y += 5f;
            text(t, 12.5f, true, BRAND);
            y += 12f;
        }
        void paragraph(String t) { text(t, 11, false, INK); }
        void field(String label, String value) {
            if (value == null || value.trim().isEmpty()) return;
            text(label + ": " + value, 10.7f, false, INK);
        }
        private void need(float height) {
            if (y + height > PAGE_HEIGHT - 55) nextPage();
        }
        void text(String source, float size, boolean bold, int color) {
            if (source == null) return;
            ink.setTypeface(bold ? Typeface.create("sans-serif", Typeface.BOLD) :
                    Typeface.create("sans-serif", Typeface.NORMAL));
            ink.setTextSize(size);
            ink.setColor(color);
            float width = PAGE_WIDTH - 2f * MARGIN;
            float lineHeight = size * 1.47f;
            String remaining = source.replace('\r', ' ').replace('\n', ' ').trim();
            while (!remaining.isEmpty()) {
                int best = remaining.length();
                while (best > 1 && ink.measureText(remaining, 0, best) > width) best--;
                if (best < remaining.length() && best > 1) {
                    int lastSpace = remaining.lastIndexOf(' ', best);
                    if (lastSpace > best / 2) best = lastSpace;
                }
                String line = remaining.substring(0, best).trim();
                if (line.isEmpty()) break;
                need(lineHeight);
                canvas.drawText(line, MARGIN, y, ink);
                y += lineHeight;
                remaining = remaining.substring(best).trim();
            }
        }
        void signature(Bitmap image) {
            float maxW = 340f, maxH = 78f;
            float scale = Math.min(maxW / image.getWidth(), maxH / image.getHeight());
            float width = Math.max(1f, image.getWidth() * scale);
            float height = Math.max(1f, image.getHeight() * scale);
            need(height + 20);
            ink.setColor(Color.WHITE);
            canvas.drawBitmap(image, null,
                    new RectF(MARGIN + 12f, y, MARGIN + 12f + width, y + height), ink);
            y += height + 8;
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
