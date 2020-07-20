import com.github.topikachu.jenkins.concurrent.latch.LatchRef;

println("define components");

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

println("save dependencies");

Set<Component> components = new HashSet<>([ocpkg, atomspace_sql, opencog_deps, postgres,
    	cogutil, atomspace, cogserver, attention, ure, pln, opencog]);

println("form the execution plan");

Component root  = componentByName(components, params.ROOT_COMPONENT);
Set<Component> built = untouched(components, Collections.singleton(root));
Map<String, Closure<?>> plan = [:];
for (Component comp : components) {

	if (built.contains(comp)) {
		continue;
	}

	List<LatchRef> reqLatches = [];
	for (Component req : comp.getRequirements()) {
		if (built.contains(req)) {
			continue;
		}
		reqLatches.add(req.getLatch());
	}

	Component inProgress = comp;
	plan[inProgress.getName()] = {
		countDownLatch(inProgress.getLatch()) {
			for (LatchRef latch : reqLatches) {
				awaitLatch(latch);
			}
			//println("starting build: " + inProgress.getName());	
			//build job: inProgress.getName()
			println("build finished: " + inProgress.getName());	
		}
	}
}

println("execute plan");

parallel(plan);

// Library functions and classes

Component componentByName(Set<Component> components, String name) {
	for (Component comp : components) {
		if (comp.getName().equals(name)) {
			return comp;
		}
	}
	throw new IllegalArgumentException("Could not find component name: " + name);
}

Set<Component> untouched(Set<Component> components, Set<Component> changed) {
	Set<Component> untouched = new HashSet<>(components);		
	untouched.removeAll(touched(components, changed));
	return untouched;
}

Set<Component> touched(Set<Component> components, Set<Component> changed) {
	Set<Component> touched = new HashSet<>();
	for (Component comp : components) {
		if (isTouched(comp, changed)) {
			touched.add(comp);
		}
	}
	return touched;
}

boolean isTouched(Component comp, Set<Component> changed) {
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

interface Component {

	String getName();
	Set<Component> getRequirements();
	LatchRef getLatch();

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

class Code extends Repo<Code> implements Component, Serializable {

	private final String name;
	private final def steps
	private LatchRef latch;

	public Code(def steps, String name) {
		this.name = name;
		this.steps = steps;
	}

	@Override
	public String getName() {
		return name;
	}

	@Override
	public Set<Component> getRequirements() {
		return Collections.emptySet();
	}

	@Override
	public LatchRef getLatch() {
		if (latch == null) {
			latch = steps.createLatch();
		}
		return latch;
	}
}

Code code(String name) {
	return new Code(this, name);
}

abstract class Job<T> extends Repo<T> implements Component, Serializable {

	protected final String name;
	protected Set<Component> requirements = new HashSet<>();
	protected final def steps;
	protected LatchRef latch;

	public Job(def steps, String name) {
		this.name = name;
		this.steps = steps;
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

	@Override
	public LatchRef getLatch() {
		if (latch == null) {
			latch = steps.createLatch();
		}
		return latch;
	}
}

class Docker extends Job<Docker> {
	public Docker(def steps, String name) {
		super(steps, name);
	}
}

Docker docker(String name) {
	return new Docker(this, name);
}

class Deb extends Job<Deb> {
	public Deb(def steps, String name) {
		super(steps, name);
	}
}

Deb deb(String name) {
	return new Deb(this, name);
}
