
use eframe::egui;
use std::sync::Arc;

pub struct LocalUI {
    state: Arc<crate::State>,
}

impl LocalUI {
    pub fn new(state: Arc<crate::State>) -> Self {
        Self { state }
    }

    pub fn run(self) {
        let options = eframe::NativeOptions {
            initial_window_size: Some(egui::vec2(800.0, 600.0)),
            min_window_size: Some(egui::vec2(400.0, 300.0)),
            ..Default::default()
        };

        eframe::run_native(
            "Eternals",
            options,
            Box::new(|_cc| Box::new(LocalUIApp::new(self.state))),
        );
    }
}

struct LocalUIApp {
    state: Arc<crate::State>,
}

impl LocalUIApp {
    fn new(state: Arc<crate::State>) -> Self {
        Self { state }
    }
}

impl eframe::App for LocalUIApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("Eternals Local UI");
            
            ui.horizontal(|ui| {
                if ui.button("Refresh").clicked() {
                    // Handle refresh
                }
                
                if ui.button("Settings").clicked() {
                    // Handle settings
                }
            });

            ui.separator();

            // Main content area
            egui::ScrollArea::vertical().show(ui, |ui| {
                // Add content here
                ui.label("Welcome to Eternals");
            });
        });
    }
}
