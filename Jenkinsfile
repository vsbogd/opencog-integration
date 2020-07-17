params = [:]
params.ROOT_COMPONENT = "atomspace";

void parallel(Map<String, Closure> stages) {
	stages.eachWithIndex{ key, value, index ->
		value.call();
	}
}

steps_copy = [:]
steps_copy.parallel = { x -> parallel x };
steps_copy.build = { x -> build x };

println ("define components");

Code ocpkg = code("ocpkg").repo(params.OCPKG_REPO).branch(params.OCPKG_BRANCH);
Code atomspace_sql = code("atomspace_sql").repo(params.ATOMSPACE_REPO).branch(params.ATOMSPACE_BRANCH);

Docker opencog_deps = docker("opencog_deps").repo(params.DOCKER_REPO).branch(params.DOCKER_BRANCH)
.requires(ocpkg);
Docker postgres = docker("postgres").repo(params.DOCKER_REPO).branch(params.DOCKER_BRANCH)
.requires(atomspace_sql);

Deb cogutil = deb("cogutil").repo(params.COGUTIL_REPO).branch(params.COGUTIL_BRANCH)
.requires(opencog_deps);
Deb atomspace = deb("atomspace").repo(params.ATOMSPACE_REPO).branch(params.ATOMSPACE_BRANCH)
.requires(opencog_deps, postgres, cogutil);
Deb cogserver = deb("cogserver").repo(params.COGSERVER_REPO).branch(params.COGSERVER_BRANCH)
.requires(opencog_deps, cogutil, atomspace);
Deb attention = deb("attention").repo(params.ATTENTION_REPO).branch(params.ATTENTION_BRANCH)
.requires(opencog_deps, cogutil, atomspace, cogserver);
Deb ure = deb("ure").repo(params.URE_REPO).branch(params.URE_BRANCH)
.requires(opencog_deps, cogutil, atomspace);
Deb pln = deb("pln").repo(params.PLN_REPO).branch(params.PLN_BRANCH)
.requires(opencog_deps, cogutil, atomspace, ure);
Deb opencog = deb("opencog").repo(params.OPENCOG_REPO).branch(params.OPENCOG_BRANCH)
.requires(opencog_deps, cogutil, atomspace, cogserver, attention, ure, pln);

println ("save dependencies");

deps = dependencies(ocpkg, atomspace_sql, opencog_deps, postgres,
    	cogutil, atomspace, cogserver, attention, ure, pln, opencog);

println ("get the list of stages and execute them");

Component root  = deps.componentByName(params.ROOT_COMPONENT);
Set<Component> ready = deps.untouched(Collections.singleton(root));
parallel deps.stagesFor(ready);

class Dependencies {

	private final def steps;
	private final Set<Component> components;

	public Dependencies(def steps, Component... components) {
		this.steps = steps;
		this.components = new HashSet<>(Arrays.asList(components));
	}

	// FIXME: what is correct type to return from this method?
	public def stagesFor(Set<Component> ready) {
		Set<Component> comps = nextComponents(ready);
		def branches = [:]
		for (Component comp : comps) {
		    branches[comp.getName()] = {
    			if (!ready.contains(comp)) {
        			println ("build: " + comp.getName());
        			//build job: comp.getName()
        			ready.add(comp);
        			// FIXME: groovy tries to call parallel as a property of
        			// Dependencies
        			steps.parallel.call(stagesFor(ready));
    			}
		    }
		}
		return branches;
	}

	public Component componentByName(String name) {
		for (Component comp : components) {
			if (comp.getName().equals(name)) {
				return comp;
			}
		}
		throw new IllegalArgumentException("Could not find component name: " + name);
	}

	private Set<Component> nextComponents(Set<Component> ready) {
		Set<Component> stageComponents = new HashSet<>();

		for (Component comp : components) {
			if (ready.contains(comp)) {
				continue;
			}
			if (!ready.containsAll(comp.getRequirements())) {
				continue;
			}

			stageComponents.add(comp);
		}

		return stageComponents;
	}

	public Set<Component> untouched(Set<Component> changed) {
		Set<Component> untouched = new HashSet<>(components);		
		untouched.removeAll(touched(changed));
		return untouched;
	}

	private Set<Component> touched(Set<Component> changed) {
		Set<Component> touched = new HashSet<>();
		for (Component comp : components) {
			if (isTouched(comp, changed)) {
				touched.add(comp);
			}
		}
		return touched;
	}

	private boolean isTouched(Component comp, Set<Component> changed) {
		if (changed.contains(comp)) {
			return true;
		}
		for (Component req : comp.getRequirements()) {
			if (isTouched(req, changed)) {
				return true;
			}
		}
		return false;
	}

}

Dependencies dependencies(Component... components) {
	return new Dependencies(steps_copy, components);
}

interface Component {

	String getName();
	Set<Component> getRequirements();

}

abstract class Repo<T> {

	protected String repo;
	protected String branch;

	public T repo(String repo) {
		this.repo = repo;	
		return (T)this;
	}

	public T branch(String branch) {
		this.branch = branch;	
		return (T)this;
	}

	@Override
	public String toString() {
		return "Repo(repo: " + repo + ", branch: " + branch + ")";
	}

}

class Code extends Repo<Code> implements Component {

	private final String name;

	public Code(String name) {
		this.name = name;
	}

	@Override
	public String getName() {
		return name;
	}

	@Override
	public Set<Component> getRequirements() {
		return Collections.emptySet();
	}

}

Code code(String name) {
	return new Code(name);
}

abstract class Job<T> extends Repo<T> implements Component {

	protected String name;
	protected Set<Component> requirements = new HashSet<>();

	public Job(String name) {
		this.name = name;
	}

	public T requires(Component... requirements) {
		this.requirements.addAll(Arrays.asList(requirements));
		return (T)this;
	}

	@Override
	public String getName() {
		return name;
	}

	@Override
	public Set<Component> getRequirements() {
		return requirements;
	}

	@Override
	public String toString() {
		return "Job(name: " + name + ")";
	}

}

class Docker extends Job<Docker> {
	public Docker(String name) {
		super(name);
	}
}

Docker docker(String name) {
	return new Docker(name);
}

class Deb extends Job<Deb> {
	public Deb(String name) {
		super(name);
	}
}

Deb deb(String name) {
	return new Deb(name);
}
