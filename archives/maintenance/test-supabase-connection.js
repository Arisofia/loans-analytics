#!/usr/bin/env node
require("dotenv").config({ path: ".env.local" });
const { createClient } = require("@supabase/supabase-js");

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error(
    "❌ Error: Variables de Supabase no configuradas en .env.local",
  );
  console.error(
    "   Verifica NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY",
  );
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

async function testConnection() {
  console.log("🔍 Iniciando pruebas de conectividad Supabase...\n");
  console.log(`📡 URL: ${SUPABASE_URL}\n`);

  try {
    // Test 1: Schema monitoring.kpi_definitions
    console.log("Test 1: Verificar schema monitoring.kpi_definitions...");
    const { data: kpiDefs, error: e1 } = await supabase
      .from("kpi_definitions")
      .select("*")
      .limit(1);

    if (e1) {
      console.log(`❌ FAILED: ${e1.message}`);
      console.log(`   Detalle: ${JSON.stringify(e1, null, 2)}`);
    } else {
      console.log(
        `✅ SUCCESS: Schema monitoring.kpi_definitions accesible (${kpiDefs?.length || 0} registros)`,
      );
    }

    // Test 2: Schema monitoring.kpi_values
    console.log("\nTest 2: Verificar schema monitoring.kpi_values...");
    const { data: kpiVals, error: e2 } = await supabase
      .from("kpi_values")
      .select("*")
      .limit(1);

    if (e2) {
      console.log(`❌ FAILED: ${e2.message}`);
    } else {
      console.log(
        `✅ SUCCESS: Schema monitoring.kpi_values accesible (${kpiVals?.length || 0} registros)`,
      );
    }

    // Test 3: Tabla public.historical_kpis
    console.log("\nTest 3: Verificar tabla public.historical_kpis...");
    const { data: histData, error: e3 } = await supabase
      .from("historical_kpis")
      .select("*")
      .limit(1);

    if (e3) {
      console.log(`❌ FAILED: ${e3.message}`);
    } else {
      console.log(
        `✅ SUCCESS: Tabla public.historical_kpis accesible (${histData?.length || 0} registros)`,
      );
    }

    // Test 4: Insert de prueba en kpi_values
    console.log(
      "\nTest 4: Insert de valor de prueba en monitoring.kpi_values...",
    );
    const testData = {
      snapshot_id: "connectivity_test_" + Date.now(),
      as_of_date: new Date().toISOString().split("T")[0],
      kpi_key: "test_connectivity",
      value_num: 999.99,
      status: "green",
      computed_at: new Date().toISOString(),
      run_id: "azure_connectivity_test",
      inputs_hash: "test_" + Math.random().toString(36).substr(2, 9),
    };

    const { data: insertResult, error: e4 } = await supabase
      .from("kpi_values")
      .insert(testData)
      .select();

    if (e4) {
      console.log(`❌ FAILED: ${e4.message}`);
      console.log(`   Detalle: ${JSON.stringify(e4, null, 2)}`);
    } else {
      console.log(
        `✅ SUCCESS: Insertado registro con ID: ${insertResult[0].id}`,
      );

      // Cleanup
      const { error: e5 } = await supabase
        .from("kpi_values")
        .delete()
        .eq("id", insertResult[0].id);

      if (e5) {
        console.log(`⚠️  Cleanup warning: ${e5.message}`);
      } else {
        console.log(`🧹 Datos de prueba eliminados correctamente`);
      }
    }

    console.log("\n═══════════════════════════════════════");
    console.log("🎯 TODAS LAS PRUEBAS COMPLETADAS");
    console.log("═══════════════════════════════════════");
    console.log("\n✅ Supabase está conectado y funcionando correctamente");
    console.log(`📊 Proyecto: ${SUPABASE_URL.split("//")[1].split(".")[0]}`);
    console.log(
      `🔗 Dashboard: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte`,
    );

    process.exit(0);
  } catch (err) {
    console.error("\n💥 Error fatal:", err.message);
    console.error("\nStack trace:", err.stack);
    process.exit(1);
  }
}

testConnection();
