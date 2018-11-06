package edu.ncsu.arguments;

import edu.ncsu.config.Settings;
import edu.ncsu.executors.models.ClassMethods;
import edu.ncsu.executors.models.Function;
import edu.ncsu.executors.models.Primitive;
import edu.ncsu.store.IArgumentStore;
import edu.ncsu.visitors.adapters.ConstantAdapter;

import java.io.File;
import java.lang.reflect.Method;
import java.util.*;
import java.util.logging.Logger;

public class ArgumentExtractor {

    private final static Logger LOGGER = Logger.getLogger(ArgumentExtractor.class.getName());

    private final static String STORAGE = "mongo";//Settings.getProperty("store");

    private String dataset;

    private IArgumentStore store;

    private int count = 0;

    /***
     * Initialize Argument Extractor
     * @param dataset - Name of the dataset
     */
    public ArgumentExtractor(String dataset) {
        this.dataset = dataset;
        if (STORAGE.equals(Settings.MONGO_STORAGE)) {
            this.store = edu.ncsu.store.mongo.ArgumentStore.loadStore(this.dataset);
        } else if (STORAGE.equals(Settings.JSON_STORAGE)) {
            this.store = edu.ncsu.store.json.ArgumentStore.loadStore(this.dataset);
        } else {
            throw new RuntimeException(String.format("Unknown store: %s", STORAGE));
        }
    }

    /**
     * Extract and store primitive arguments for a dataset.
     * @param javaFiles - List of paths fo java files.
     */
    public void extractAndStorePrimitiveArguments(List<String> javaFiles) {
        LOGGER.info(String.format("Number of java files: %d", javaFiles.size()));
        ConstantAdapter adapter;
        Map<Primitive, Set<Object>> constantsMap = new HashMap<>();
        Map<Primitive, Set<Object>> fileConstantsMap;
        for (String javaFile: javaFiles) {
            try {
                adapter = new ConstantAdapter(javaFile);
                fileConstantsMap = adapter.getConstantsMap();
                for(Primitive primitive: fileConstantsMap.keySet()) {
                    Set<Object> values = new HashSet<>();
                    if (constantsMap.containsKey(primitive)) {
                        values = constantsMap.get(primitive);
                    }
                    values.addAll(fileConstantsMap.get(primitive));
                    constantsMap.put(primitive, values);
                }
            } catch (Exception e) {
                LOGGER.severe(String.format("Failed to process : %s", javaFile));
                throw e;
            }
        }
        LOGGER.info("PRIOR TO SAVING !!!!");
        for (Primitive primitive: constantsMap.keySet()) {
            System.out.println(primitive + " : " + constantsMap.get(primitive).size());
        }
        this.store.savePrimitiveArguments(constantsMap);
        constantsMap = this.store.loadPrimitiveArguments();
        LOGGER.info("====================");
        LOGGER.info("POST SAVING !!!!");
        for (Primitive primitive: constantsMap.keySet()) {
            System.out.println(primitive + " : " + constantsMap.get(primitive).size());
        }
    }

    /**
     * Generate arguments and save for the java file.
     * @param javaFile - Path of the java file.
     */
    public void generateForJavaFile(String javaFile) {
        ClassMethods classMethods = new ClassMethods(this.dataset, javaFile);
        for (Method method: classMethods.getMethods()) {
            Function function = new Function(this.dataset, method, classMethods.getMethodBodies().get(method.getName()));
            if (!function.isValidArgs())
                continue;
            String key = function.makeArgumentsKey();
            if (!this.store.fuzzedKeyExists(key)) {
                LOGGER.info(String.format("Storing Key: %s", key));
                List<Object> arguments = ArgumentGenerator.generateArgumentsForFunction(this.dataset, function);
                if (arguments != null) {
                    this.store.saveFuzzedArguments(key, arguments);
                    this.count += 1;
                }

            }
        }
    }

    /**
     * Store fuzzed arguments for list of java files and dataset
     * @param javaFiles - List of path of java files
     */
    public void storeFuzzedArguments(List<String> javaFiles) {
        LOGGER.info("Generating random args. Here we go ....");
        store.deleteFuzzedArguments();
        for (String javaFile: javaFiles) {
            LOGGER.info(String.format("Running for %s", javaFile));
            generateForJavaFile(javaFile);
        }
        System.out.println("Count = " + count);
    }
}