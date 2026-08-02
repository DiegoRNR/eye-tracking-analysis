convert_rda_to_csv <- function(rda_path, output_dir = NULL) {
  if (!file.exists(rda_path)) {
    stop(paste("El archivo no existe:", rda_path))
  }

  message(paste("--> Procesando:", rda_path))

  # Crear un entorno temporal para evitar sobreescribir variables existentes
  temp_env <- new.env()
  loaded_objects <- load(rda_path, envir = temp_env)

  if (length(loaded_objects) == 0) {
    warning(paste("No se encontraron objetos en:", rda_path))
    return(NULL)
  }

  # Determinar la carpeta de salida
  if (is.null(output_dir)) {
    output_dir <- dirname(rda_path)
  }

  base_name <- tools::file_path_sans_ext(basename(rda_path))
  converted_files <- c()

  for (obj_name in loaded_objects) {
    obj <- get(obj_name, envir = temp_env)

    if (is.data.frame(obj) || is.matrix(obj)) {
      if (length(loaded_objects) == 1) {
        csv_filename <- paste0(base_name, ".csv")
      } else {
        csv_filename <- paste0(base_name, "_", obj_name, ".csv")
      }

      output_csv <- file.path(output_dir, csv_filename)
      write.csv(obj, output_csv, row.names = FALSE)
      message(paste("    [OK] Guardado en:", output_csv))
      converted_files <- c(converted_files, output_csv)
    } else {
      warning(paste("El objeto '", obj_name, "' no es una tabla o dataframe. Se omitió."))
    }
  }

  return(invisible(converted_files))
}
args <- commandArgs(trailingOnly = TRUE)

if (length(args) > 0) {
  target_file <- args[1]
  convert_rda_to_csv(target_file)
} else if (sys.nframe() == 0) {
  message("Buscando archivos .rda en el directorio 'data/'...")
  rda_files <- list.files("data", pattern = "\\.(rda|RData)$", full.names = TRUE, recursive = TRUE)

  if (length(rda_files) == 0) {
    message("No se encontraron archivos .rda en 'data/'. Por favor especifica una ruta.")
  } else {
    for (f in rda_files) {
      convert_rda_to_csv(f)
    }
  }
}
