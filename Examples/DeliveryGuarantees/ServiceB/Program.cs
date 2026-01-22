using System.Diagnostics;
using System.Diagnostics.Metrics;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using ServiceB;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

string otelEndpoint = builder.Configuration["OpenTelemetry:Endpoint"]!;

Meter meter = new("DeliveryGuarantees.ServiceB", "1.0.0");
Counter<long> messagesReceivedCounter = meter.CreateCounter<long>("delivery_messages_received_total");

builder.Services.AddOpenTelemetry()
    .ConfigureResource(x => x
        .AddService("delivery-receiver"))
    .WithTracing(tracing => tracing
        .AddAspNetCoreInstrumentation()
        .AddOtlpExporter(options => { options.Endpoint = new(otelEndpoint); }))
    .WithMetrics(metrics => metrics
        .AddMeter("DeliveryGuarantees.ServiceB")
        .AddAspNetCoreInstrumentation()
        .AddRuntimeInstrumentation()
        .AddOtlpExporter((exporterOptions, metricReaderOptions) =>
        {
            exporterOptions.Endpoint = new(otelEndpoint);
            metricReaderOptions.PeriodicExportingMetricReaderOptions.ExportIntervalMilliseconds = 1000;
        }));

WebApplication app = builder.Build();
app.UseSwagger();
app.UseSwaggerUI();

app.MapPost("/api/message", (MessageRequest request) =>
{
    messagesReceivedCounter.Add(1, new TagList { { "message_id", request.MessageId } });
    return Results.Ok();
});

app.Run();